# **MuseTalk Architecture Weights Directory**

## **Overview**

This directory acts as the central repository for the primary neural network weights driving the ultra-realistic lip-sync rendering engine.

## **Required Files**

Depending on your configuration, the following files must be present:

* unet.pth (The primary MuseTalk UNet model, ensure cross-attention dimensionality matches your config.json)  
* dw-ll\_ucoco\_384.pth (DWPose landmark detection model)  
* config.json (UNet structural blueprint)

## **Source**

Reference the official TencentARC repository for the latest weights:

[TencentARC/MuseTalk](https://huggingface.co/TencentARC/MuseTalk)