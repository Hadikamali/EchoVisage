# **GFPGAN Facial Restoration Weights**

## **Overview**

This directory contains the essential pre-trained neural network weights for the GFPGAN (Generative Facial Prior GAN) restoration pipeline. These components perform critical computer vision tasks, specifically face detection and segmentation, which are required to upscale and enhance facial details in the generated video frames.

## **Included Models**

### **1\. Face Detection**

* **File**: detection\_Resnet50\_Final.pth  
* **Function**: This ResNet50-based model is responsible for identifying the location and bounding boxes of faces within each frame. It ensures that the restoration pipeline correctly focuses on facial regions.

### **2\. Face Parsing**

* **File**: parsing\_parsenet.pth  
* **Function**: This model performs semantic segmentation of the facial region. It identifies specific facial landmarks and regions (such as skin, eyes, and lips) to guide the generative process for high-fidelity restoration.

## **Maintenance**

These weights are required for the GFPGANer class initialization. Ensure that:

1. The file names match exactly as listed above.  
2. The file paths are correctly configured within your inference scripts.  
3. These weights are kept in this directory to maintain the modular structure of the EchoVisage processing pipeline.

## **Source**

These weights are derived from the official TencentARC GFPGAN implementation. If files are corrupted or missing, refer to the official repository for re-acquisition.