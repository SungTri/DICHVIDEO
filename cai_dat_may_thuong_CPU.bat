@echo off
chcp 65001 >nul
echo ===================================================
echo CAI DAT MOI TRUONG CHO MAY THUONG (CHI DUNG CPU)
echo ===================================================
echo.
echo Buoc 1/3: Kich hoat moi truong ao (venv)...
if not exist "venv\Scripts\activate" (
    echo [Loi] Khong tim thay moi truong ao 'venv'.
    pause
    exit /b
)
call venv\Scripts\activate
echo.
echo Buoc 2/3: Go phien ban CUDA (neu co) de tranh xung dot...
pip uninstall -y torch torchvision torchaudio
echo.
echo Buoc 3/3: Cai dat PyTorch ban nhe danh cho CPU...
pip install torch torchvision torchaudio
echo.
echo Buoc 4/4: Cai dat cac thu vien loi (Whisper, Demucs...)
pip install demucs
pip install -r requirements.txt
echo.
echo ===================================================
echo HOAN TAT! May cua ban da san sang.
echo ===================================================
pause
