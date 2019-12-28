import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bot-frost",
    version="2.0.0",
    description="The official bot for the Husker Discord server.",
    url="https://github.com/refekt/Bot-Frost",
    author='/u/refekt',
    author_email='refekt@gmail.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    license='MIT',
    zip_safe=False
)