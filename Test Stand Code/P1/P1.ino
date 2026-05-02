#include <Servo.h>
#include "HX711.h"
const int LOADCELL_DOUT_PIN = 2; //Green DT 2
const int LOADCELL_SCK_PIN = 3;  //Yellow SDK 3  
// const float bias = 616266;
// const float lamda =405;

const float bias= -387987.00;
const float lamda=1266;

const int num_blade = 3;

HX711 scale;
Servo esc;
int val1;
int val2;

const int escMin = 1000;        // Range
const int escMax = 2000;        
const float Kp1 = 0.05;
volatile int passCount = 0;
unsigned long previousMillis = 0;

const unsigned long interval = 3000;
int escInput = 1000;
double rpm = 0;
bool passDetected = false;
int targetRPM = 0;


void setup() {
  pinMode(6,INPUT);
  Serial.begin(9600);
  esc.attach(7);
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  esc.writeMicroseconds(1000); // Initialize the ESC with no throttle
  delay(1000);
}



void loop() {
  val1=digitalRead(6);
  // int escValue = map(val2, 0, 1024, 2000, 1000);
  // esc.writeMicroseconds(escValue);
  if (val1==1 && !passDetected) {
    passCount++;
    passDetected = true;
  }
  if (val1==0 && passDetected) {
    passDetected = false;
  }
    // Serial.print(val1);
    // Serial.print("         ");
    // Serial.println(val2);
    // delay(500);
    // Calibration

  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    unsigned long timeBetweenMillis = currentMillis - previousMillis;
    rpm = passCount*60000/ timeBetweenMillis/num_blade; // Assuming one ductape Convert milliseconds to RPM
    previousMillis = currentMillis;
    passCount = 0;

    // Serial.print("TimeStamp:");
    // Serial.println(millis());
    Serial.print("ESC:");
    Serial.println(escInput);
    Serial.print("Measured_RPM:");
    Serial.println(rpm);
    Serial.print("Expected_RPM:");
    Serial.println(targetRPM);
    Serial.print("Thrust:");
    Serial.println((scale.get_units()-bias)/lamda, 1); //bias&lamda are two constant for the load cell calibrated using another code.
    Serial.println();
    //Output on the Serial monitor have the format
    //TimeStamp: <value1> ms
    //ESC: <value2> impulse width (microsecond)
    //Measured_RPM: <value3>
    //Expected_RPM: <value4>
    //Thrust: <value5> g


  if (targetRPM > 0) { // Only adjust if a target RPM is set
      float error = targetRPM - rpm;
      escInput += min(50.0, Kp1 * error); // Adjust ESC input based on the error
      escInput = constrain(escInput, escMin, escMax); // Limit to ESC range

      esc.writeMicroseconds(escInput); // Apply the adjusted ESC signal
    }
  if (targetRPM==0){
    escInput=0;
    esc.writeMicroseconds(1000);
  }
  }
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    targetRPM = input.toInt();
    // Serial.print("Target RPM set to");
    // Serial.println(targetRPM);
  }


}
