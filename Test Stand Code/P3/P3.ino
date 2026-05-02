#include <Servo.h>
#include "HX711.h"
#include <math.h>

const int LOADCELL_DOUT_PIN = 2; // Green DT 2
const int LOADCELL_SCK_PIN = 3;  // Yellow SCK 3
const int RPM_SENSOR_PIN = 6;
const int ESC_PIN = 7;
const int POWER_PIN = A4;

const float thrustBias = -329473.00;
const float thrustLamda = 436*981;

const float powerBias = 499.70;
const float powerLamda = 1.28;

const int num_blade = 2;

HX711 scale;
Servo esc;
int val1;

const int escMin = 1000;
const int escMax = 2000;
const float Kp1 = 0.05;
const float Kp2 = 0.02;
const float rpmErrorThreshold = 200.0;

volatile int passCount = 0;

const unsigned long thrustPeriod = 500000;   // 500 ms
const unsigned long windowPeriod = 3000000;

int escInput = escMin;
double rpm = 0;
bool passDetected = false;
int targetRPM = 0;

unsigned long windowStartMicros = 0;
unsigned long previousThrustMicros = 0;

unsigned long blockedMicros = 0;

int sampleCount = 0;
int thrustCount = 0;

double powerMean = 0;
double powerM2 = 0;
double thrustMean = 0;
double thrustM2 = 0;
double thrustReadMean = 0;
double thrustReadM2 = 0;

String serialBuffer = "";

double correctThrust(double rawValue) {
  return (rawValue - thrustBias) / thrustLamda;
}

double correctPower(double rawValue) {
  return (rawValue - powerBias) / powerLamda;
}

void updateStats(double x, double &mean, double &M2, int n) {
  double delta = x - mean;
  mean += delta / n;
  double delta2 = x - mean;
  M2 += delta * delta2;
}

double getStd(double M2, int n) {
  if (n < 2) return 0;
  return sqrt(M2 / (n - 1));
}

void resetWindow() {
  passCount = 0;
  sampleCount = 0;
  thrustCount = 0;
  blockedMicros = 0;
  powerMean = 0;
  powerM2 = 0;
  thrustMean = 0;
  thrustM2 = 0;
  thrustReadMean = 0;
  thrustReadM2 = 0;
  windowStartMicros = micros();
}

void stopMotor() {
  targetRPM = 0;
  escInput = escMin;
  rpm = 0;
  esc.writeMicroseconds(escMin);
}

void updateESC() {
  if (targetRPM > 0) {
    float error = targetRPM - rpm;
    float kappa;

    if (abs(error) < rpmErrorThreshold) {
      kappa = Kp2;
    } else {
      kappa = Kp1;
    }

    escInput += constrain(kappa * error, -50.0, 50.0);
    escInput = constrain(escInput, escMin, escMax);
    esc.writeMicroseconds(escInput);
  } else {
    stopMotor();
  }
}

void executeStage() {
  unsigned long now = micros();
  unsigned long totalTimeMicros = now - windowStartMicros;
  unsigned long compensatedTimeMicros = totalTimeMicros - blockedMicros;

  if (compensatedTimeMicros == 0) return;

  rpm = passCount * 60000000.0 / compensatedTimeMicros / num_blade;

  Serial.print("ESC:");
  Serial.println(escInput);
  Serial.print("Measured_RPM:");
  Serial.println(rpm);
  Serial.print("Expected_RPM:");
  Serial.println(targetRPM);

  Serial.print("Thrust_Average_N:");
  Serial.println(thrustMean, 3);
  Serial.print("Thrust_STD_N:");
  Serial.println(getStd(thrustM2, thrustCount), 3);

  Serial.print("Power_Average_W:");
  Serial.println(powerMean, 2);
  Serial.print("Power_STD_W:");
  Serial.println(getStd(powerM2, sampleCount), 2);
  Serial.println("");

  updateESC();

  resetWindow();
}

bool checkSerialInput() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      if (serialBuffer.length() > 0) {
        int newRPM = serialBuffer.toInt();
        serialBuffer = "";

        targetRPM = newRPM;

        if (targetRPM <= 0) {
          stopMotor();
        }

        return true;
      }
    } else {
      serialBuffer += c;
    }
  }

  return false;
}

void setup() {
  pinMode(RPM_SENSOR_PIN, INPUT);
  Serial.begin(9600);

  esc.attach(ESC_PIN);
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);

  stopMotor();
  delay(1000);

  previousThrustMicros = micros();
  windowStartMicros = previousThrustMicros;
}

void loop() {
  if (checkSerialInput()) {
    executeStage();
    return;
  }

  unsigned long currentMicros = micros();

  val1 = digitalRead(RPM_SENSOR_PIN);

  if (val1 == 1 && !passDetected) {
    passCount++;
    passDetected = true;
  }

  if (val1 == 0 && passDetected) {
    passDetected = false;
  }

  sampleCount++;

  int rawPower = analogRead(POWER_PIN);
  double powerValue = correctPower(rawPower);
  updateStats(powerValue, powerMean, powerM2, sampleCount);

  if (currentMicros - previousThrustMicros >= thrustPeriod) {
    previousThrustMicros = currentMicros;

    unsigned long thrustReadStart = micros();
    double rawThrust = scale.get_units();
    unsigned long thrustReadEnd = micros();

    unsigned long thrustReadTime = thrustReadEnd - thrustReadStart;
    blockedMicros += thrustReadTime;

    double thrustValue = correctThrust(rawThrust);

    thrustCount++;
    updateStats(thrustValue, thrustMean, thrustM2, thrustCount);
    updateStats((double)thrustReadTime, thrustReadMean, thrustReadM2, thrustCount);
  }

  if (currentMicros - windowStartMicros >= windowPeriod) {
    executeStage();
  }
}