<template>
  <div class="pages">
    <div class="page-header">
      <h2>📘 Tutorial</h2>
      <p>How to get started with Posture Monitor Pro in a few simple steps</p>
    </div>

    <!-- Quick steps -->
    <div class="steps-grid">
      <div class="card step-card">
        <div class="step-number">1</div>
        <h3>🎥 Open the Monitor</h3>
        <p>Go to the <strong>Monitor</strong> tab. Allow your browser to use the camera when prompted. Your video stays on your device — nothing is uploaded.</p>
      </div>

      <div class="card step-card">
        <div class="step-number">2</div>
        <h3>▶️ Start monitoring</h3>
        <p>Click <strong>Start</strong>. The app detects your body landmarks and shows live posture metrics. A green status means the posture engine is connected.</p>
      </div>

      <div class="card step-card">
        <div class="step-number">3</div>
        <h3>🎯 Calibrate</h3>
        <p>Sit in your best comfortable posture, then run <strong>Manual Calibration</strong> and click on the requested body points. This adapts the metrics to your morphology.</p>
      </div>

      <div class="card step-card">
        <div class="step-number">4</div>
        <h3>🔔 React to alerts</h3>
        <p>When your posture drifts from your baseline, an on-screen alert (and optional sound) reminds you to adjust. Just sit back up straight.</p>
      </div>

      <div class="card step-card">
        <div class="step-number">5</div>
        <h3>📊 Track progress</h3>
        <p>Open the <strong>Dashboard</strong> to review your posture history, trends, and time spent in good posture.</p>
      </div>

      <div class="card step-card">
        <div class="step-number">6</div>
        <h3>🔐 Control your data</h3>
        <p>In <strong>Privacy &amp; Data</strong> you can export or delete everything at any time. All processing happens locally on your computer.</p>
      </div>
    </div>

    <!-- Understanding the metrics -->
    <div class="card section-card">
      <h3>Understanding the metrics</h3>
      <div class="metric-help">
        <div class="metric-help-row">
          <span class="metric-help-name">Spine Angle</span>
          <span class="metric-help-desc">How upright your back is. Higher slouching increases this value away from your baseline.</span>
        </div>
        <div class="metric-help-row">
          <span class="metric-help-name">Shoulder Symmetry</span>
          <span class="metric-help-desc">Whether your shoulders are level. A drop on one side lowers the percentage.</span>
        </div>
        <div class="metric-help-row">
          <span class="metric-help-name">Neck Angle</span>
          <span class="metric-help-desc">The forward bend of your neck. Looking down at a phone raises this value.</span>
        </div>
        <div class="metric-help-row">
          <span class="metric-help-name">Head Tilt L/R</span>
          <span class="metric-help-desc">Sideways tilt of your head, left or right of center.</span>
        </div>
        <div class="metric-help-row">
          <span class="metric-help-name">Head Forward</span>
          <span class="metric-help-desc">How far your head leans forward of your shoulders ("tech neck").</span>
        </div>
      </div>
    </div>

    <!-- Tips -->
    <div class="card section-card">
      <h3>Tips for the best results</h3>
      <ul class="tips-list">
        <li>Place your camera roughly at eye level, facing you, with your upper body visible.</li>
        <li>Make sure the room is well lit so landmarks are detected reliably.</li>
        <li>Re-calibrate if you change your chair, desk, or camera position.</li>
        <li>You can switch tabs while monitoring — tracking keeps running in the background.</li>
      </ul>
    </div>

    <!-- Disclaimer -->
    <div class="card disclaimer-card">
      <h3>⚠️ Important</h3>
      <p>
        Posture Monitor Pro is <strong>not a medical device</strong>. The metrics are indicative aids
        to encourage better posture habits and do not constitute medical advice or diagnosis.
        Use of the application is at your own responsibility. For any health concern, consult a
        qualified healthcare professional.
      </p>
    </div>
  </div>
</template>

<script setup>
// Static informational page — no logic required.
</script>

<style scoped>
.page-header {
  margin-bottom: 30px;
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e2e8f0;
}

.step-card {
  position: relative;
  padding-top: 28px;
}

.step-card h3 {
  margin-bottom: 10px;
}

.step-card p {
  color: #718096;
  font-size: 14px;
  margin: 0;
}

.step-number {
  position: absolute;
  top: -14px;
  left: 20px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.4);
}

.section-card {
  margin-bottom: 20px;
}

.section-card h3 {
  margin-bottom: 16px;
}

.metric-help {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metric-help-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-bottom: 12px;
  border-bottom: 1px solid #edf2f7;
}

.metric-help-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.metric-help-name {
  font-weight: 700;
  color: #2d3748;
}

.metric-help-desc {
  color: #718096;
  font-size: 14px;
}

.tips-list {
  margin: 0;
  padding-left: 20px;
  color: #718096;
}

.tips-list li {
  margin-bottom: 8px;
  font-size: 14px;
}

.disclaimer-card {
  border-left: 4px solid #f6ad55;
  background: #fffaf0;
}

.disclaimer-card h3 {
  margin-bottom: 10px;
  color: #c05621;
}

.disclaimer-card p {
  color: #744210;
  font-size: 14px;
  margin: 0;
}
</style>
