from setuptools import find_packages, setup

package_name = 'terrarover_bridge'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Killa Coders',
    maintainer_email='killa.coders@spaceapps.org',
    description='ROS 2 Jazzy bridge node for TerraRover Webots simulation',
    license='MIT',
    entry_points={
        'console_scripts': [
            'terrarover_bridge_node = terrarover_bridge.bridge_node:main',
        ],
    },
)
