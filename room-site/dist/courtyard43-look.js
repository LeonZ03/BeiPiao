// One Courtyard43-only calibration. Lighting uses linear values; grading runs
// once after ACES and sRGB encoding. No shared Yongwang constants are changed.
export const COURTYARD_LOOK=Object.freeze({
  version:'quality21',exposure:1.00,
  environmentBase:.21,environmentGain:.14,
  skyBase:.25,skyGain:.18,
  windowBase:.035,windowGain:.71,
  bounceBase:.14,bounceGain:.14,
  saturation:.89,contrast:1.035,
  warmth:[.013,.003,-.009],shadowLift:[.010,.009,.008],
  highlightReduction:.010,vignette:.028,
});
