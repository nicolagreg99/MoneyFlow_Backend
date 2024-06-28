#!/bin/bash

PROJECT_NAME="app-money"
VERSION="1.0.0"

# Creare una directory temporanea per il pacchetto
mkdir -p ${PROJECT_NAME}-${VERSION}

# Copiare i file del progetto nella directory temporanea
cp -r app.py config.py requirements.txt ReadME database api ${PROJECT_NAME}-${VERSION}

# Creare l'archivio tar.gz
tar -czvf ${PROJECT_NAME}-${VERSION}.tar.gz ${PROJECT_NAME}-${VERSION}

# Rimuovere la directory temporanea
rm -rf ${PROJECT_NAME}-${VERSION}
