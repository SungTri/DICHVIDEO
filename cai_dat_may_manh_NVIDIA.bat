@echo off
chcp 65001 >nul
echo ===================================================
echo CAI DAT MOI TRUONG CHO MAY CO CARD DO HOA NVIDIA
echo ===================================================
echo.
echo Buoc 1/4: Kich hoat moi truong ao (venv)...
if not exist "venv\Scripts\activate" (
    echo [Loi] Khong tim thay moi truong ao 'venv'.
    pause
    exit /b
)
call venv\Scripts\activate
echo.
echo Buoc 2/4: Go cai dat phien ban PyTorch CPU cu (neu co)...
pip uninstall -y torch torchvision torchaudio
echo.
echo Buoc 3/4: Cai dat PyTorch chuan CUDA 12.1 (ho tro NVIDIA)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
echo.
echo Buoc 4/4: Cai dat cac thu vien loi (Whisper, Demucs...)
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 demucs
pip install -r requirements.txt
echo.
echo ===================================================
echo HOAN TAT! May cua ban da duoc nang cap de chay GPU!
echo ===================================================
pause
