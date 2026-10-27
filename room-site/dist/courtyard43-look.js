// One Courtyard43-only calibration. Lighting uses linear values; grading runs
// once after ACES and sRGB encoding. No shared Yongwang constants are changed.
export const COURTYARD_LOOK=Object.freeze({
  version:'tonal34',exposure:1.18,
  // Keep snow brightness at the north opening instead of stacking uniform
  // IBL, hemisphere and room-centre fill over every surface equally.
  // Closed-curtain visibility and the single switched lamp remain separate.
  environmentBase:.16,environmentGain:.25,
  skyBase:.22,skyGain:.28,skyColor:'#f0f3f6',
  groundClosedColor:'#776756',groundOpenColor:'#a49a8d',
  daylightBase:.025,daylightGain:.90,daylightShadow:.66,daylightColor:'#f3f2eb',
  windowBase:.035,windowGain:1.45,
  bounceBase:.12,bounceGain:.32,bounceColor:'#f3e5d1',
  saturation:.99,contrast:1.09,
  // Warm middle values, restrained cool shadows and neutral snow highlights.
  warmth:[.018,.008,-.005],shadowLift:[0,0,0],
  highlightReduction:0,vignette:.006,
});
