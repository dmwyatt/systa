poetry run sphinx-build -M clean source build -c ./
REM poetry run sphinx-apidoc --force -o ./source ../src
poetry run sphinx-build -M doctest source build -c ./
poetry run sphinx-build -M html source build -c ./
