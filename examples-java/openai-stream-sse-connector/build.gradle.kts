plugins {
    application
}

group = "io.vastar.examples"
version = "1.0.0"

java {
    sourceCompatibility = JavaVersion.VERSION_11
    targetCompatibility = JavaVersion.VERSION_11
}

repositories {
    mavenCentral()
}

dependencies {
    // Use local SDK JAR (Fat JAR with all dependencies)
    implementation(files("../libs/vastar-connector-sdk-java-0.1.0-all.jar"))

    // Logging implementation
    runtimeOnly("ch.qos.logback:logback-classic:1.4.14")

    // YAML configuration
    implementation("org.yaml:snakeyaml:2.2")
}

application {
    mainClass.set("io.vastar.examples.openai.OpenAIStreamConnector")
}

tasks.withType<JavaCompile> {
    options.encoding = "UTF-8"
}

// Task to run with simulator
tasks.register<JavaExec>("runSimulator") {
    group = "application"
    description = "Run with RAI Simulator"
    classpath = sourceSets.main.get().runtimeClasspath
    mainClass.set("io.vastar.examples.openai.OpenAIStreamConnector")
    environment("USE_REAL_OPENAI", "false")
}

// Task to run with real OpenAI
tasks.register<JavaExec>("runOpenAI") {
    group = "application"
    description = "Run with Real OpenAI API"
    classpath = sourceSets.main.get().runtimeClasspath
    mainClass.set("io.vastar.examples.openai.OpenAIStreamConnector")
    environment("USE_REAL_OPENAI", "true")
    // OPENAI_API_KEY should be set in environment
}

