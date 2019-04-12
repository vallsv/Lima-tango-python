cp scripts/LimaCCDs $PREFIX/bin
mkdir -p $SP_DIR/Lima/Server && cp *.py $SP_DIR/Lima/Server/
mkdir -p $SP_DIR/Lima/Server/camera && cp camera/__init__.py $SP_DIR/Lima/Server/camera/
mkdir -p $SP_DIR/Lima/Server/plugins && cp -R plugins $SP_DIR/Lima/Server/
