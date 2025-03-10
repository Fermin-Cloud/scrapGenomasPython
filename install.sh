#!/bin/bash

# Lista de bibliotecas a instalar
libs=(
    "libwoff2-1"
    "libvpx6"
    "libevent-2.1-6"
    "libopus0"
    "libgstreamer-plugins-base1.0-0"
    "libgstreamer-plugins-good1.0-0"
    "libgstreamer-plugins-bad1.0-0"
    "libflite1"
    "libflite-usenglish1"
    "libflite-cmu-grapheme-lang1"
    "libflite-cmu-grapheme-lex1"
    "libflite-cmu-indic-lang1"
    "libflite-cmu-indic-lex1"
    "libflite-cmulex1"
    "libflite-cmu-time-awb1"
    "libflite-cmu-us-awb1"
    "libflite-cmu-us-kal16"
    "libflite-cmu-us-kal1"
    "libflite-cmu-us-rms1"
    "libflite-cmu-us-slt1"
    "libwebp6"
    "libharfbuzz-icu0"
)

# Archivo de log para bibliotecas fallidas
failed_libs="failed_libraries.log"

# Limpiar el archivo de bibliotecas fallidas si ya existe
> "$failed_libs"

# Intentar instalar cada biblioteca
for lib in "${libs[@]}"; do
    echo "Intentando instalar $lib..."
    if sudo apt-get install -y "$lib"; then
        echo "$lib instalado correctamente."
    else
        echo "Error al instalar $lib." | tee -a "$failed_libs"
    fi
done

# Mostrar el resultado
echo "El script ha terminado. Las bibliotecas que no se pudieron instalar están en $failed_libs."
