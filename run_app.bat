@echo off
chcp 65001 > nul
echo ====================================================================
echo  KHỞI ĐỘNG HỆ THỐNG DỰ BÁO GIÁ CỔ PHIẾU RNN (MÔ HÌNH MVC)
echo ====================================================================
echo.

IF EXIST "C:\Users\PC ASUS\miniconda3\envs\cnn_env\python.exe" (
    echo [1/2] Sử dụng môi trường cnn_env...
    "C:\Users\PC ASUS\miniconda3\envs\cnn_env\python.exe" app.py
) ELSE (
    echo [1/2] Sử dụng Python mặc định trên máy...
    python app.py
)

pause
