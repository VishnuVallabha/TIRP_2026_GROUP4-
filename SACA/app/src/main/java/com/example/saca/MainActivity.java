package com.example.saca;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;

import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    Button startButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialise TTS once for the whole app — matches desktop _init_tts()
        SacaTTS.init(this);

        startButton = findViewById(R.id.startButton);
        startButton.setOnClickListener(v -> {
            // Speak welcome message — matches desktop cover screen
            SacaTTS.speak("Welcome to SACA. A health triage tool for the Yirrkala Community.");
            Intent intent = new Intent(MainActivity.this, LanguageActivity.class);
            startActivity(intent);
        });
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        SacaTTS.shutdown();
    }
}
