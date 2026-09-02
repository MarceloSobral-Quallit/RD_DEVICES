@echo off
setlocal

set "TOOLS_DIR=%~dp0"
set "ROOT_DIR=%TOOLS_DIR%.."
set "VENV_PY=%ROOT_DIR%\.venv\Scripts\python.exe"

pushd "%ROOT_DIR%" || (
    echo Erro: nao foi possivel acessar a raiz do projeto.
    pause
    exit /b 1
)

:: ---------------------------------------------------------------------------
:: Verificação/criação automática do ambiente virtual antes do build
:: ---------------------------------------------------------------------------
if not exist "%VENV_PY%" (
    echo [VENV] Ambiente virtual nao encontrado. Criando...
    python -m venv .venv
    if errorlevel 1 ( py -3 -m venv .venv )
    if errorlevel 1 (
        echo [VENV] ERRO: Falha ao criar o ambiente virtual.
        pause & exit /b 1
    )
    "%VENV_PY%" -m pip install --upgrade pip --quiet
    if exist requirements.txt (
        "%VENV_PY%" -m pip install -r requirements.txt
        if errorlevel 1 ( echo [VENV] AVISO: Falha ao instalar dependencias. )
    ) else (
        "%VENV_PY%" -m pip install pyinstaller --quiet
    )
    echo [VENV] Ambiente virtual criado.
) else (
    echo [VENV] Ambiente virtual OK.
)

"%VENV_PY%" tools\build_release.py --component all --bump build --build-type onefile --sign
set "EXIT_CODE=%ERRORLEVEL%"

popd

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Build falhou com codigo %EXIT_CODE%.
) else (
    echo.
    echo Build concluido com sucesso.
)

echo.
pause
exit /b %EXIT_CODE%
