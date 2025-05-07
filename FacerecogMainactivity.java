package com.example.comparision;

import android.content.Intent;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.provider.MediaStore;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.bumptech.glide.Glide;

public class MainActivity extends AppCompatActivity {

    private Button btnUpload, btnCapture, btnCompare;
    private ImageView imageCaptured, imageUploaded;
    private Uri uploadedImageUri;
    private Bitmap capturedImageBitmap;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        btnUpload = findViewById(R.id.btnUpload);
        btnCapture = findViewById(R.id.btnCapture);
        btnCompare = findViewById(R.id.btnCompare); // Initialize compare button
        imageCaptured = findViewById(R.id.imageCaptured);
        imageUploaded = findViewById(R.id.imageUploaded);

        // Initialize TensorFlow model
        FaceUtils.initTensorFlow(this);

        btnUpload.setOnClickListener(v -> openGallery());
        btnCapture.setOnClickListener(v -> openCamera());

        // Add Compare button logic
        btnCompare.setOnClickListener(v -> {
            if (uploadedImageUri == null || capturedImageBitmap == null) {
                Toast.makeText(this, "Upload and Capture both images first", Toast.LENGTH_SHORT).show();
            } else {
                processFaceVerification(capturedImageBitmap);
            }
        });
    }

    private void openGallery() {
        Intent intent = new Intent(Intent.ACTION_PICK, MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
        startActivityForResult(intent, 101);
    }

    private void openCamera() {
        Intent intent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
        startActivityForResult(intent, 102);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode == RESULT_OK && data != null) {
            if (requestCode == 101) {
                uploadedImageUri = data.getData();
                Glide.with(this).load(uploadedImageUri).into(imageUploaded);
            } else if (requestCode == 102) {
                capturedImageBitmap = (Bitmap) data.getExtras().get("data");
                imageCaptured.setImageBitmap(capturedImageBitmap);
            }
        }
    }

    private void processFaceVerification(Bitmap capturedImage) {
        if (uploadedImageUri == null && capturedImage == null) {
            Toast.makeText(this, "Please select or capture an image first", Toast.LENGTH_SHORT).show();
            return;
        }

        FaceUtils.detectFaceAndCompare(capturedImage, uploadedImageUri, this);
    }
}
