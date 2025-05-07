package com.example.comparision;

import android.content.Context;
import android.graphics.Bitmap;
import android.net.Uri;
import android.provider.MediaStore;
import android.util.Log;
import android.widget.Toast;

import org.tensorflow.lite.Interpreter;
import org.tensorflow.lite.support.common.FileUtil;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.MappedByteBuffer;

public class FaceUtils {

    private static Interpreter tflite;
    private static final String MODEL_PATH = "facenet.tflite"; // Ensure this model is 160x160 input & float32
    private static final String TAG = "FaceUtils";
    private static final int IMAGE_SIZE = 160;

    public static void initTensorFlow(Context context) {
        try {
            if (tflite == null) {
                MappedByteBuffer tfliteModel = FileUtil.loadMappedFile(context, MODEL_PATH);
                tflite = new Interpreter(tfliteModel);
                Log.d(TAG, "TensorFlow Lite model loaded successfully.");
            }
        } catch (Exception e) {
            e.printStackTrace();
            Toast.makeText(context, "Model initialization failed", Toast.LENGTH_SHORT).show();
        }
    }

    public static void detectFaceAndCompare(Bitmap capturedImage, Uri uploadedImageUri, Context context) {
        if (tflite == null) initTensorFlow(context);

        if (capturedImage == null || uploadedImageUri == null) {
            Toast.makeText(context, "Invalid image data", Toast.LENGTH_SHORT).show();
            return;
        }

        float[] capturedEmbeddings = extractEmbeddings(capturedImage);
        float[] uploadedEmbeddings = extractEmbeddings(uploadedImageUri, context);

        if (capturedEmbeddings != null && uploadedEmbeddings != null) {
            float similarity = cosineSimilarity(capturedEmbeddings, uploadedEmbeddings);
            int percentage = (int) (similarity * 100);
            Toast.makeText(context, "Similarity: " + percentage + "%", Toast.LENGTH_LONG).show();
        } else {
            Toast.makeText(context, "Embedding extraction failed", Toast.LENGTH_SHORT).show();
        }
    }

    private static float[] extractEmbeddings(Bitmap bitmap) {
        Bitmap resized = Bitmap.createScaledBitmap(bitmap, IMAGE_SIZE, IMAGE_SIZE, true);
        ByteBuffer inputBuffer = convertBitmapToByteBuffer(resized);

        float[][] embeddings = new float[1][128]; // FaceNet default
        tflite.run(inputBuffer, embeddings);
        return embeddings[0];
    }

    private static float[] extractEmbeddings(Uri imageUri, Context context) {
        try {
            Bitmap bitmap = MediaStore.Images.Media.getBitmap(context.getContentResolver(), imageUri);
            return extractEmbeddings(bitmap);
        } catch (Exception e) {
            Log.e(TAG, "Error loading image from URI", e);
            return null;
        }
    }

    private static ByteBuffer convertBitmapToByteBuffer(Bitmap bitmap) {
        ByteBuffer buffer = ByteBuffer.allocateDirect(4 * IMAGE_SIZE * IMAGE_SIZE * 3);
        buffer.order(ByteOrder.nativeOrder());
        buffer.rewind();

        int[] intValues = new int[IMAGE_SIZE * IMAGE_SIZE];
        bitmap.getPixels(intValues, 0, IMAGE_SIZE, 0, 0, IMAGE_SIZE, IMAGE_SIZE);

        for (int i = 0; i < intValues.length; ++i) {
            int val = intValues[i];
            buffer.putFloat(((val >> 16) & 0xFF) / 255.0f); // R
            buffer.putFloat(((val >> 8) & 0xFF) / 255.0f);  // G
            buffer.putFloat((val & 0xFF) / 255.0f);         // B
        }

        return buffer;
    }

    private static float cosineSimilarity(float[] a, float[] b) {
        float dot = 0f, normA = 0f, normB = 0f;
        for (int i = 0; i < a.length; i++) {
            dot += a[i] * b[i];
            normA += a[i] * a[i];
            normB += b[i] * b[i];
        }
        return dot / ((float) (Math.sqrt(normA) * Math.sqrt(normB)));
    }
}
