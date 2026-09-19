// Shader additions apply only to Blender-tagged exterior materials. The approved
// room fog, exposure, light positions and static sun-shadow proxies are untouched.
export function installExteriorSurface(material){
  if(!material.userData.exteriorSurface)return;
  const previous=material.onBeforeCompile,priorKey=material.customProgramCacheKey();
  material.onBeforeCompile=(shader,renderer)=>{
    previous.call(material,shader,renderer);
    shader.fragmentShader=shader.fragmentShader.replace('#include <fog_fragment>',`
      #ifdef USE_FOG
        float courtyardHaze=smoothstep(18.,90.,vFogDepth)*.55;
        gl_FragColor.rgb=mix(gl_FragColor.rgb,fogColor,courtyardHaze);
      #endif
    `);
    if(material.userData.leafSurface){
      // Thin leaf transmission follows the existing sun. A bounded diffuse term,
      // not additive glow or transparent cards; all geometry stays depth-writing.
      shader.fragmentShader=shader.fragmentShader.replace('#include <lights_fragment_end>',`#include <lights_fragment_end>
        #if NUM_DIR_LIGHTS > 0
          float leafBacklight=pow(max(0.,dot(-normal,directionalLights[0].direction)),2.);
          reflectedLight.directDiffuse+=diffuseColor.rgb*directionalLights[0].color*(.20*leafBacklight);
        #endif
      `);
    }
  };
  material.customProgramCacheKey=()=>priorKey+'-exterior31-'+(material.userData.leafSurface?'leaf':'surface');
}
