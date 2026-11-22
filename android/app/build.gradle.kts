plugins {
    id("com.android.application")
}

android {
    namespace = "io.github.andytwoods.wristpointer"
    compileSdk = 36
    defaultConfig {
        applicationId = "io.github.andytwoods.wristpointer"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "0.1"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation("com.garmin.connectiq:ciq-companion-app-sdk:2.0.3@aar")
}
