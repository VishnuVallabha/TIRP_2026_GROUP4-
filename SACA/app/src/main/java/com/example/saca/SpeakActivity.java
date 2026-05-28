package com.example.saca;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

public class SpeakActivity extends AppCompatActivity {

    String language = "english";
    int    age      = 30;
    String gender   = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_speak);

        language = getIntent().getStringExtra("language");
        age      = getIntent().getIntExtra("age", 30);
        gender   = getIntent().getStringExtra("gender");
        if (language == null) language = "english";
        if (gender   == null) gender   = "";

        TextView backButton = findViewById(R.id.backButton);
        backButton.setText(AppLanguage.back(language));
        backButton.setOnClickListener(v -> finish());

        Button start = findViewById(R.id.startSpeak);
        start.setOnClickListener(v -> {
            Intent intent = new Intent(SpeakActivity.this, SpeakQuestionsActivity.class);
            intent.putExtra("language", language);
            intent.putExtra("age",      age);
            intent.putExtra("gender",   gender);
            startActivity(intent);
        });
    }
}