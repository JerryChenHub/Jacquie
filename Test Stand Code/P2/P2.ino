#include <Servo.h>
#include "HX711.h"

// ----------------------------------------------------------------
// Pin definitions and constants
// ----------------------------------------------------------------
const int LOADCELL_DOUT_PIN = 2;
const int LOADCELL_SCK_PIN  = 3;
//const float bias  = 616266;
//const float lamda = 405;

const float bias = 636885;
const float lamda = 95.44;

const int num_blade = 3;

HX711 scale;
Servo esc;
int val1;
const int RPM_SENSOR_PIN = 6;
const int ESC_PIN  = 7;
const int escMin   = 1000;
const int escMax   = 2000;
const float Kp1    = 0.05;

volatile unsigned long passCount = 0; 
unsigned long previousMillis = 0;
unsigned long previousMillis2 = 0;
const unsigned long interval = 3000;
int escInput = 1000;
double rpm=0;
volatile bool passDetected= false;
int targetRPM=0;

struct TestResult {
  int rpm;
  int duration;
  float averageThrust;
};
TestResult testResults[20];
int testCount = 0;


void setup() {
  Serial.begin(9600);
  pinMode(RPM_SENSOR_PIN, INPUT);
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  esc.attach(ESC_PIN);
  esc.writeMicroseconds(escMin);
  delay(2000);
  Serial.print("The number of balde is: ");
  Serial.println(num_blade);
  Serial.println("Ready to read config lines (RPM Duration)...");

}

// ----------------------------------------------------------------
// Main Loop: read configuration lines from Serial
// ----------------------------------------------------------------
void loop() {
  while (Serial.available() > 0) {
    String pair = Serial.readStringUntil(';');
    pair.trim();
    if (pair.length() == 0) {
      continue;
    }
    int commaIndex = pair.indexOf(',');
    if (commaIndex == -1) {
      // If there's no comma, we could check if it's "done" or treat it as invalid
      if (pair.equalsIgnoreCase("done")) {
        Serial.println("Done with all tests. Now printing results...");
        esc.writeMicroseconds(escMin);
        printAllResults();
        return; // or break;
      } else {
        Serial.print("Invalid format: ");
        Serial.println(pair);
      }
      continue; 
    }

    String rpmString = pair.substring(0, commaIndex);
    String durString = pair.substring(commaIndex + 1);

    int rpmVal = rpmString.toInt();
    int durationVal = durString.toInt();
    
    TestResult allResults[10];
    int resultCount = 0;
    float avgThrust=runTest(rpmVal, durationVal);
    testResults[testCount].rpm = rpmVal;
    testResults[testCount].duration = durationVal;
    testResults[testCount].averageThrust = avgThrust;
    testCount++;


  }
}

float runTest(int rpmVal, int durationVal){
  int duration=durationVal;
  targetRPM = rpmVal;
  bool stable1=false;
  Serial.print("Setting target RPM = ");
  Serial.println(targetRPM);
  while(true){
      val1=digitalRead(6);//For my sensor, when the object pass, it returns 1
      val1=!val1;//for the lab's sensor, when the object pass it returns 0, so we make it consistent here.
      
      if (val1==1 && !passDetected) {
          passCount++;
          passDetected = true;}
      if (val1==0 && passDetected) {
          passDetected = false;}
      unsigned long currentMillis = millis();
      if (currentMillis - previousMillis >= interval) {
        unsigned long timeBetweenMillis = currentMillis - previousMillis;
        rpm = passCount*60000/ timeBetweenMillis/num_blade;
        previousMillis = currentMillis;
        passCount = 0;
        Serial.print("ESC:"); //Impulse width send to the ESC(microsecond)
        Serial.println(escInput);
        Serial.print("Measured_RPM:");
        Serial.println(rpm);
        Serial.println();


      if (targetRPM > 0) { // Only adjust if a target RPM is set
          float error = targetRPM - rpm;
          if (abs(error)<=20){
            if (stable1){
            break;}
            else{stable1=true;}
            }
          escInput += min(50.0, Kp1 * error); // Adjust ESC input based on the error
          escInput = constrain(escInput, escMin, escMax); // Limit to ESC range
          esc.writeMicroseconds(escInput); // Apply the adjusted ESC signal
        }
      if (targetRPM==0){
        escInput=0;
        esc.writeMicroseconds(1000);}}
  }




  Serial.print("Reached RPM = ");
  Serial.println(rpm);
  float averageThrust=0.0;
  float Thrust;
  float _count=0;
  while(true){
    unsigned long currentMillis2 = millis();
    if (currentMillis2 - previousMillis2 >= 1000){
      Thrust=(scale.get_units()-bias)/lamda;
      previousMillis2 = currentMillis2;
      _count++;
      averageThrust=(_count-1)/_count*averageThrust+Thrust/_count;
      Serial.print("Thrust(g) = ");
      Serial.println(Thrust);
      Serial.print("Average Thrust(g) = ");
      Serial.println(averageThrust);
    }
    if (_count>=duration){break;}
  } 
  ;
return averageThrust;
}

void printAllResults() {
  Serial.println("====== ALL TEST RESULTS ======");
  for (int i = 0; i < testCount; i++) {
    Serial.print("Test #");
    Serial.print(i + 1);
    Serial.print(": RPM=");
    Serial.print(testResults[i].rpm);
    Serial.print(", Duration=");
    Serial.print(testResults[i].duration);
    Serial.print("s, Avg Thrust=");
    Serial.print(testResults[i].averageThrust);
    Serial.println(" g");
  }
  Serial.println("=============================");
}
