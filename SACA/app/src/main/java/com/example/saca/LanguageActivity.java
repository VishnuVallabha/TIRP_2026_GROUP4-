package com.example.saca;

import android.content.Intent;
import android.os.Bundle;
import android.widget.LinearLayout;

import androidx.appcompat.app.AppCompatActivity;

public class LanguageActivity extends AppCompatActivity {

    LinearLayout backButton, englishCard, yolnguCard;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_language);

        backButton = findViewById(R.id.backButton);
        englishCard = findViewById(R.id.englishCard);
        yolnguCard = findViewById(R.id.yolnguCard);

        // Back button
        backButton.setOnClickListener(v -> finish());

        // English selected
        englishCard.setOnClickListener(v -> openMethod("english"));

        // Yolngu selected
        yolnguCard.setOnClickListener(v -> openMethod("yolngu"));
    }

    private void openMethod(String language) {

        Intent intent = new Intent(
                LanguageActivity.this,
                MethodActivity.class
        );

        intent.putExtra("language", language);

        startActivity(intent);
    }
}