package com.example.saca;

import android.content.Intent;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

public class MethodActivity extends AppCompatActivity {

    String language = "english";
    int    age      = 30;
    String gender   = "";

    TextView backButton, titleText, subtitleText;
    TextView method1Title, method1Sub1, method1Sub2;
    TextView method2Title, method2Sub1, method2Sub2;
    TextView method3Title, method3Sub1, method3Sub2;
    LinearLayout symptomIdentification, speakSymptom, typeSymptom;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_method);

        language = getIntent().getStringExtra("language");
        age      = getIntent().getIntExtra("age", 30);
        gender   = getIntent().getStringExtra("gender");
        if (language == null) language = "english";
        if (gender   == null) gender   = "";

        backButton           = findViewById(R.id.backButton);
        titleText            = findViewById(R.id.titleText);
        subtitleText         = findViewById(R.id.subtitleText);
        method1Title         = findViewById(R.id.method1Title);
        method1Sub1          = findViewById(R.id.method1Sub1);
        method1Sub2          = findViewById(R.id.method1Sub2);
        method2Title         = findViewById(R.id.method2Title);
        method2Sub1          = findViewById(R.id.method2Sub1);
        method2Sub2          = findViewById(R.id.method2Sub2);
        method3Title         = findViewById(R.id.method3Title);
        method3Sub1          = findViewById(R.id.method3Sub1);
        method3Sub2          = findViewById(R.id.method3Sub2);
        symptomIdentification= findViewById(R.id.symptomIdentification);
        speakSymptom         = findViewById(R.id.speakSymptom);
        typeSymptom          = findViewById(R.id.typeSymptom);

        backButton.setText(AppLanguage.back(language));
        titleText.setText(AppLanguage.methodTitle(language));
        subtitleText.setText(AppLanguage.methodSubtitle(language));
        method1Title.setText(AppLanguage.symptomIdentification(language));
        method1Sub1.setText(AppLanguage.symptomIdSub1(language));
        method1Sub2.setText(AppLanguage.symptomIdSub2(language));
        method2Title.setText(AppLanguage.speak(language));
        method2Sub1.setText(AppLanguage.speakSub1(language));
        method2Sub2.setText(AppLanguage.speakSub2(language));
        method3Title.setText(AppLanguage.type(language));
        method3Sub1.setText(AppLanguage.typeSub1(language));
        method3Sub2.setText(AppLanguage.typeSub2(language));

        backButton.setOnClickListener(v -> finish());

        symptomIdentification.setOnClickListener(v -> {
            Intent i = new Intent(this, BodyPartActivity.class);
            i.putExtra("language", language); i.putExtra("age", age); i.putExtra("gender", gender);
            startActivity(i);
        });
        speakSymptom.setOnClickListener(v -> {
            Intent i = new Intent(this, SpeakActivity.class);
            i.putExtra("language", language); i.putExtra("age", age); i.putExtra("gender", gender);
            startActivity(i);
        });
        typeSymptom.setOnClickListener(v -> {
            Intent i = new Intent(this, TypeSymptomActivity.class);
            i.putExtra("language", language); i.putExtra("age", age); i.putExtra("gender", gender);
            startActivity(i);
        });
    }
}