export function addToilet(c,bath){
  const {THREE,mat,box,cylinder,ellipsoid}=c;
  const root=new THREE.Group();root.name='porcelain-toilet';root.position.set(-.69,0,2.83);bath.add(root);
  const porcelain=mat('#f4f3ec',.23),seatMaterial=mat('#f9f7ed',.32),chrome=mat('#b6bfc0',.25,{metalness:.65});
  ellipsoid(0,.155,-.018,.127,.155,.166,porcelain,root);
  // A continuous section runs up the exterior, over the rim and down inside.
  const section=[[0,.105],[.085,.105],[.125,.20],[.162,.285],[.185,.34],[.19,.385],[.184,.409],[.171,.417],[.156,.409],[.151,.393],[.132,.346],[.10,.311],[.055,.298],[.032,.279],[0,.275]];
  const curve=new THREE.SplineCurve(section.map(([r,y])=>new THREE.Vector2(r,y)));
  const bowl=new THREE.Mesh(new THREE.LatheGeometry(curve.getPoints(112),80),porcelain);bowl.scale.z=1.34;bowl.position.z=-.095;bowl.castShadow=bowl.receiveShadow=true;root.add(bowl);
  const water=new THREE.Mesh(new THREE.CircleGeometry(.061,48),mat('#a7c8c3',.15,{transparent:true,opacity:.65}));water.rotation.x=-Math.PI/2;water.scale.y=1.35;water.position.set(0,.303,-.095);root.add(water);
  function oval(w,h,hole=false){
    const shape=new THREE.Shape();shape.absellipse(0,0,w,h,0,Math.PI*2,false);
    if(hole){const inner=new THREE.Path();inner.absellipse(0,-.003,.130,.188,0,Math.PI*2,true);shape.holes.push(inner);}
    return new THREE.ExtrudeGeometry(shape,{depth:.014,bevelEnabled:true,bevelSegments:3,steps:1,bevelSize:.004,bevelThickness:.004,curveSegments:64});
  }
  const seat=new THREE.Mesh(oval(.187,.255,true),seatMaterial);seat.name='flat-open-toilet-seat';seat.rotation.x=-Math.PI/2;seat.position.set(0,.421,-.095);seat.castShadow=seat.receiveShadow=true;root.add(seat);
  box(.328,.365,.145,porcelain,0,.568,.249,root,.028);
  box(.342,.024,.160,porcelain,0,.759,.249,root,.014);
  cylinder(.026,.026,.006,chrome,0,.774,.249,root,32);
  box(.002,.001,.043,seatMaterial,0,.778,.249,root);
  for(const x of [-.078,.078]){
    box(.038,.016,.045,seatMaterial,x,.416,.116,root,.006);
    const hinge=cylinder(.012,.012,.046,chrome,x,.440,.119,root,24);hinge.rotation.z=Math.PI/2;
  }
  const pivot=new THREE.Group();pivot.name='raised-solid-toilet-lid';pivot.position.set(0,.445,.128);pivot.rotation.x=1.60;root.add(pivot);
  const lid=new THREE.Mesh(oval(.187,.254),seatMaterial);lid.rotation.x=-Math.PI/2;lid.position.z=-.222;lid.castShadow=lid.receiveShadow=true;pivot.add(lid);
  // Small underside stops sit on the lid's inner face, above the seat when closed.
  for(const x of [-.125,.125])box(.028,.008,.055,seatMaterial,x,-.009,-.30,pivot,.005);
  return root;
}
