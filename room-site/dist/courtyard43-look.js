// One Courtyard43-only calibration. Lighting uses linear values; grading runs
// once after ACES and sRGB encoding. No shared Yongwang constants are changed.
export const COURTYARD_LOOK=Object.freeze({
  version:'daylight28',exposure:1.18,
  // Snow raises broad daylight through the open north window. Retain the
  // closed-curtain floor and the existing single switched ceiling light.
  environmentBase:.21,environmentGain:.36,
  skyBase:.25,skyGain:.40,skyColor:'#f0f3f6',
  groundClosedColor:'#776756',groundOpenColor:'#b6b0a5',
  windowBase:.035,windowGain:1.35,
  bounceBase:.14,bounceGain:.49,bounceColor:'#f3e5d1',
  saturation:.97,contrast:1.00,
  // Warm middle values, restrained cool shadows and neutral snow highlights.
  warmth:[.012,.007,-.002],shadowLift:[.002,.003,.004],
  highlightReduction:0,vignette:.006,
});
