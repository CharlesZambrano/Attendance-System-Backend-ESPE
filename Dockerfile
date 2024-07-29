# Utilizar una imagen base de NVIDIA que incluya TensorRT y CUDA 12.6
FROM nvcr.io/nvidia/tensorrt:22.12-py3

# Instalar dependencias adicionales
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar Flask y otras dependencias de Python
RUN pip3 install --upgrade pip
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

# Copiar el contenido del proyecto al contenedor
COPY . /app
WORKDIR /app

# Exponer el puerto que usará Flask
EXPOSE 5000

# Comando para ejecutar la aplicación Flask
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
