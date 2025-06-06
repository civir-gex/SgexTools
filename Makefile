run:
	uvicorn main:app --reload

test:
	PYTHONPATH=. pytest -v


# Elimina archivos de caché y temporales
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +