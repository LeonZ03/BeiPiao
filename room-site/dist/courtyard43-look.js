// One Courtyard43-only calibration. Lighting uses linear values; grading runs
// once after ACES and sRGB encoding. No shared Yongwang constants are changed.
export const COURTYARD_LOOK=Object.freeze({
  version:'winter23',exposure:1.18,
  // Snow raises broad daylight through the open north window. Retain the
  // closed-curtain floor and the existing single switched ceiling light.
  environmentBase:.21,environmentGain:.19,
  skyBase:.25,skyGain:.25,
  windowBase:.035,windowGain:1.00,
  bounceBase:.14,bounceGain:.24,
  saturation:.91,contrast:1.04,
  // Warm middle values, restrained cool shadows and neutral snow highlights.
  warmth:[.023,.009,-.007],shadowLift:[.008,.010,.014],
  highlightReduction:.006,vignette:.018,
});
