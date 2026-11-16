#!/usr/bin/env python3
"""Exporta un repositorio a un Markdown con el contenido completo de archivos de texto.

Uso:
  cd ~/terrarover_rover
  python3 /ruta/exportar_terrarover_markdown.py
  python3 /ruta/exportar_terrarover_markdown.py --output docs/TERRAROVER_TODO.md

Los archivos binarios se inventarían (no se insertan en base64).
Los directorios de dependencias/cachés y archivos potencialmente secretos se omiten.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

IGNORED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", "node_modules",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache",
    ".tox", ".nox", "dist", "build", ".terraform", ".ipynb_checkpoints",
}

BINARY_EXTENSIONS = {
    ".tif", ".tiff", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp",
    ".ico", ".svgz", ".pdf", ".zip", ".gz", ".7z", ".rar", ".tar",
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav",
    ".glb", ".fbx", ".blend", ".dae", ".ply", ".npy", ".npz",
    ".pth", ".pt", ".pkl", ".pickle", ".sqlite", ".sqlite3", ".db",
    ".so", ".dll", ".exe", ".bin", ".woff", ".woff2", ".ttf",
}

LANG_BY_EXT = {
    ".py": "python", ".wbt": "vrml", ".proto": "vrml", ".urdf": "xml",
    ".xacro": "xml", ".xml": "xml", ".html": "html", ".htm": "html",
    ".css": "css", ".js": "javascript", ".ts": "typescript",
    ".sh": "bash", ".bash": "bash", ".zsh": "bash",
    ".json": "json", ".ipynb": "json", ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml", ".ini": "ini", ".cfg": "ini", ".md": "markdown",
    ".rst": "rst", ".csv": "csv", ".tsv": "tsv", ".sql": "sql",
    ".tex": "latex", ".cpp": "cpp", ".h": "cpp", ".hpp": "cpp",
    ".c": "c", ".java": "java", ".gitignore": "gitignore",
    ".dockerignore": "gitignore", ".dockerfile": "dockerfile",
    ".svg": "xml", ".obj": "text", ".stl": "text",
}

SECRET_FILENAMES = {
    ".env", "id_rsa", "id_ed25519", "credentials.json", "token.json",
    "secrets.json", "service-account.json", "service_account.json",
}
SECRET_EXTENSIONS = {".pem", ".key", ".p12", ".pfx", ".jks", ".keystore"}


def is_secret(name: str) -> bool:
    low = name.lower()
    return (
        low in SECRET_FILENAMES
        or low.startswith(".env.")
        or Path(low).suffix in SECRET_EXTENSIONS
    )


def collect_paths(root: Path, output: Path):
    files: list[Path] = []
    skipped: list[str] = []
    for folder, dirs, names in os.walk(root, followlinks=False):
        folder_path = Path(folder)
        for name in list(dirs):
            full = folder_path / name
            if name in IGNORED_DIRS or full.is_symlink():
                dirs.remove(name)
                skipped.append(full.relative_to(root).as_posix() + "/")
        dirs.sort(key=str.casefold)
        for name in sorted(names, key=str.casefold):
            full = folder_path / name
            if full.resolve() == output or full.is_symlink():
                if full.is_symlink():
                    skipped.append(full.relative_to(root).as_posix() + " (enlace simbólico)")
                continue
            if is_secret(name):
                skipped.append(full.relative_to(root).as_posix() + " (potencial secreto)")
                continue
            if full.is_file():
                files.append(full)
    return sorted(files, key=lambda x: x.relative_to(root).as_posix().casefold()), skipped


def binary_file(path: Path) -> bool:
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    with path.open("rb") as source:
        sample = source.read(8192)
    if b"\x00" in sample:
        return True
    if not sample:
        return False
    control_bytes = sum(b < 32 and b not in (9, 10, 13, 12, 8) for b in sample)
    return (control_bytes / len(sample)) > 0.06


def hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def fence_for(path: Path) -> str:
    """Usa una cerca de ~ suficientemente larga para cualquier texto del archivo."""
    longest = 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as stream:
        for line in stream:
            for match in re.finditer(r"~+", line):
                longest = max(longest, len(match.group()))
    return "~" * max(3, longest + 1)


def language(path: Path) -> str:
    if path.name == "Dockerfile":
        return "dockerfile"
    if path.name in {"Makefile", "GNUmakefile"}:
        return "makefile"
    return LANG_BY_EXT.get(path.suffix.lower(), "text")


def render_tree(paths: list[str], rootname: str) -> str:
    tree: dict = {}
    for rel in paths:
        node = tree
        for part in rel.split("/"):
            node = node.setdefault(part, {})

    lines = [rootname + "/"]

    def walk(node: dict, prefix: str):
        children = sorted(node.items(), key=lambda item: (not bool(item[1]), item[0].lower()))
        for i, (name, subtree) in enumerate(children):
            last = i == len(children) - 1
            lines.append(prefix + ("└── " if last else "├── ") + name + ("/" if subtree else ""))
            if subtree:
                walk(subtree, prefix + ("    " if last else "│   "))

    walk(tree, "")
    return "\n".join(lines)


def write_file_contents(out, path: Path):
    fence = fence_for(path)
    out.write(f"{fence}{language(path)}\n")
    last_char = "\n"
    with path.open("r", encoding="utf-8", errors="replace", newline="") as stream:
        for line in stream:
            # Normaliza CRLF exclusivamente en el informe, sin tocar el original.
            normalized = line.replace("\r\n", "\n").replace("\r", "\n")
            out.write(normalized)
            if normalized:
                last_char = normalized[-1]
    if last_char != "\n":
        out.write("\n")
    out.write(f"{fence}\n\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convierte la parte textual de TerraRover a un Markdown íntegro")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Directorio del proyecto (por defecto: actual)")
    parser.add_argument("--output", type=Path, default=Path("TERRAROVER_DOCUMENTACION_COMPLETA.md"), help="Markdown a generar dentro del proyecto")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"No existe el directorio: {root}")
    output = args.output.expanduser()
    if not output.is_absolute():
        output = root / output
    output = output.resolve()
    if not output.is_relative_to(root):
        parser.error("Por seguridad, el archivo de salida debe estar dentro del proyecto")
    output.parent.mkdir(parents=True, exist_ok=True)

    files, skipped = collect_paths(root, output)
    text_files: list[Path] = []
    binary_files: list[Path] = []
    unreadable: list[str] = []
    for path in files:
        try:
            (binary_files if binary_file(path) else text_files).append(path)
        except OSError as exc:
            unreadable.append(f"{path.relative_to(root).as_posix()}: {exc}")

    total_bytes = sum(p.stat().st_size for p in text_files + binary_files)
    generated = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    with output.open("w", encoding="utf-8", newline="\n") as out:
        out.write(f"# TerraRover — Inventario y código fuente completo\n\n")
        out.write(f"> Proyecto: `{root.name}`  \n")
        out.write(f"> Generado: {generated}  \n")
        out.write(f"> Archivos de texto completos: **{len(text_files)}**  \n")
        out.write(f"> Archivos binarios inventariados: **{len(binary_files)}**  \n")
        out.write(f"> Tamaño total inventariado: **{total_bytes / 1024 / 1024:.2f} MiB**\n\n")
        out.write("Este documento contiene **íntegramente** el código fuente y los archivos ")
        out.write("legibles como texto del proyecto, sin resumir ni omitir líneas. Los binarios ")
        out.write("(DEM GeoTIFF, mapas, imágenes, vídeos, etc.) se listan, pero requieren ")
        out.write("conservar sus archivos originales: Markdown no puede sustituirlos. ")
        out.write("Se omiten cachés, entornos virtuales y archivos potencialmente secretos.\n\n")
        out.write("## 1. Árbol de archivos\n\n")
        out.write("```text\n" + render_tree([p.relative_to(root).as_posix() for p in text_files + binary_files], root.name) + "\n```\n\n")
        out.write("## 2. Código fuente y archivos de texto — contenido íntegro\n\n")
        for index, path in enumerate(text_files, start=1):
            relative = path.relative_to(root).as_posix()
            out.write(f"### 2.{index}. `{relative.replace('`', 'ˋ')}`\n\n")
            out.write(f"- **Tamaño:** {path.stat().st_size:,} bytes\n")
            out.write(f"- **SHA-256:** `{hash_file(path)}`\n\n")
            try:
                write_file_contents(out, path)
            except (OSError, UnicodeError) as exc:
                out.write(f"> No se pudo leer el contenido: {html.escape(str(exc))}\n\n")
                unreadable.append(f"{relative}: {exc}")
            if index % 10 == 0:
                print(f"Procesados {index}/{len(text_files)} archivos de texto...", flush=True)

        out.write("## 3. Archivos binarios y recursos que deben conservarse\n\n")
        out.write("Los enlaces siguientes apuntan a los originales dentro del repositorio. ")
        out.write("No están embebidos en el Markdown para evitar perder la estructura de los archivos.\n\n")
        if binary_files:
            out.write("| Archivo | Tamaño (bytes) | SHA-256 |\n|---|---:|---|\n")
            for path in binary_files:
                relative = path.relative_to(root).as_posix()
                safe_label = relative.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
                # Ruta calculada desde el propio Markdown (también funciona en docs/).
                url = quote(Path(os.path.relpath(path, output.parent)).as_posix(), safe="/")
                out.write(f"| [{safe_label}](<{url}>) | {path.stat().st_size:,} | `{hash_file(path)}` |\n")
            out.write("\n")
        else:
            out.write("No se encontraron archivos binarios.\n\n")
        out.write("## 4. Exclusiones y precauciones\n\n")
        out.write("Excluidos deliberadamente: directorios de dependencias/cachés, ")
        out.write("archivos de credenciales potenciales y enlaces simbólicos.\n\n")
        if skipped:
            out.write("```text\n" + "\n".join(sorted(skipped)) + "\n```\n\n")
        if unreadable:
            out.write("### Archivos con errores de lectura\n\n```text\n")
            out.write("\n".join(unreadable) + "\n```\n\n")
        out.write("**Antes de compartir:** revisa que no haya claves, tokens, contraseñas, ")
        out.write("información privada o rutas sensibles dentro de archivos de código/configuración.\n\n")
        out.write("**Nota:** un documento Markdown no ejecuta por sí mismo Webots ni ")
        out.write("reemplaza DEM, texturas, bibliotecas o el proyecto original.\n")

    size = output.stat().st_size
    print("\nEXPORTACIÓN COMPLETADA")
    print("Archivo:", output)
    print("Código/texto:", len(text_files), "| Binarios inventariados:", len(binary_files))
    print(f"Tamaño del Markdown: {size / 1024 / 1024:.2f} MiB")
    if unreadable:
        print("ADVERTENCIA: Hay archivos con errores; consulta la sección 4")
    print("Puedes abrirlo en VS Code u Obsidian. Revísalo antes de publicarlo.")


if __name__ == "__main__":
    main()
