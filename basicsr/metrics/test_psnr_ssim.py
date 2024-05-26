import cv2
import torch
import pytest
from basicsr.metrics import calculate_psnr, calculate_ssim
from basicsr.metrics.psnr_ssim import calculate_psnr_pt, calculate_ssim_pt
from basicsr.utils import img2tensor

# Пути к изображениям
IMG_PATH = 'D:/tets_model/0001x8.png'
IMG_PATH2 = 'D:/tets_model/0001.png'
CROP_BORDER = 4
TEST_Y_CHANNEL = False

def test():
    img = cv2.imread(IMG_PATH, cv2.IMREAD_UNCHANGED)
    img2 = cv2.imread(IMG_PATH2, cv2.IMREAD_UNCHANGED)
    img2 = cv2.resize(img2, (img.shape[1], img.shape[0]))
    # --------------------- Numpy ---------------------
    psnr = calculate_psnr(img, img2, crop_border=CROP_BORDER, input_order='HWC', test_y_channel=TEST_Y_CHANNEL)
    ssim = calculate_ssim(img, img2, crop_border=CROP_BORDER, input_order='HWC', test_y_channel=TEST_Y_CHANNEL)
    print(f'\tNumpy\tPSNR: {psnr:.6f} dB, \tSSIM: {ssim:.6f}')

    # --------------------- PyTorch (CPU) ---------------------
    img = img2tensor(img / 255., bgr2rgb=True, float32=True).unsqueeze_(0)
    img2 = img2tensor(img2 / 255., bgr2rgb=True, float32=True).unsqueeze_(0)

    psnr_pth = calculate_psnr_pt(img, img2, crop_border=CROP_BORDER, test_y_channel=TEST_Y_CHANNEL)
    ssim_pth = calculate_ssim_pt(img, img2, crop_border=CROP_BORDER, test_y_channel=TEST_Y_CHANNEL)
    print(f'\tTensor (CPU) \tPSNR: {psnr_pth[0]:.6f} dB, \tSSIM: {ssim_pth[0]:.6f}')

    psnr_pth = calculate_psnr_pt(
        torch.repeat_interleave(img, 2, dim=0),
        torch.repeat_interleave(img2, 2, dim=0),
        crop_border=CROP_BORDER,
        test_y_channel=TEST_Y_CHANNEL)
    ssim_pth = calculate_ssim_pt(
        torch.repeat_interleave(img, 2, dim=0),
        torch.repeat_interleave(img2, 2, dim=0),
        crop_border=CROP_BORDER,
        test_y_channel=TEST_Y_CHANNEL)
    print(f'\tTensor (GPU batch) \tPSNR: {psnr_pth[0]:.6f}, {psnr_pth[1]:.6f} dB,'
          f'\tSSIM: {ssim_pth[0]:.6f}, {ssim_pth[1]:.6f}')
