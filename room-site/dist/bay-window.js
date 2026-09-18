import {bayWindow as bay} from './room-layout.js?v=blender18';

// Reference topology: deep pink returns, one broad stone sill, rear-set white
// glazing, fixed left light and a slightly inward-opening upper-right casement.
export function addBayWindow({THREE,world,M,mat,box,cylinder,rod}){
  const root=new THREE.Group();root.name='photo-guided-recessed-bay-window';world.add(root);
  const cx=(bay.left+bay.right)/2,width=bay.right-bay.left;
  const stone=new THREE.MeshPhysicalMaterial({color:'#e9dcbc',roughness:.28,clearcoat:.23,clearcoatRoughness:.30});
  const sillBack=bay.frameZ-.062,sillDepth=bay.sillFrontZ-sillBack;
  const sill=box(width+.042,.043,sillDepth,stone,cx,bay.bottom+.0215,(sillBack+bay.sillFrontZ)/2,root,.011);
  sill.name='deep-rounded-stone-bay-sill';
  // The small underside return makes a real rounded stone edge over the pink apron.
  box(width+.024,.014,.028,stone,cx,bay.bottom+.003,bay.sillFrontZ-.016,root,.005);

  const frameMat=mat('#e6e8e1',.35,{metalness:.12});
  const fixed=new THREE.Group();fixed.name='bay-fixed-white-window-frame';root.add(fixed);
  const left=bay.left+.035,right=bay.right-.035,bottom=bay.bottom+.065,top=bay.top-.035;
  const height=top-bottom,mid=(top+bottom)/2,z=bay.frameZ;
  for(const x of [left,right])box(.060,height+.060,.112,frameMat,x,mid,z,fixed,.003);
  for(const y of [bottom,top])box(right-left+.060,.060,.112,frameMat,(left+right)/2,y,z,fixed,.003);
  box(.055,height,.112,frameMat,bay.mullionX,mid,z,fixed,.0025);
  const rightWidth=right-bay.mullionX,rx=(right+bay.mullionX)/2;
  box(rightWidth,.053,.108,frameMat,rx,bay.transomY,z,fixed,.0025);
  const gasket=mat('#68716c',.67);
  // Fine glazing beads, rather than heavy gray frame members.
  const pane=(x1,x2,y1,y2,name)=>{
    const g=new THREE.Group();g.name=name;fixed.add(g);
    for(const x of [x1,x2])box(.008,y2-y1,.011,gasket,x,(y1+y2)/2,z+.008,g);
    for(const y of [y1,y2])box(x2-x1,.008,.011,gasket,(x1+x2)/2,y,z+.008,g);
    box(x2-x1-.009,y2-y1-.009,.007,M.glass,(x1+x2)/2,(y1+y2)/2,z-.006,g);
  };
  pane(left+.030,bay.mullionX-.029,bottom+.030,top-.031,'bay-left-fixed-glass');
  pane(bay.mullionX+.029,right-.031,bottom+.031,bay.transomY-.029,'bay-lower-right-fixed-glass');

  const sash=new THREE.Group();sash.name='inward-opening-window-sash';
  const hingeX=right-.002,sashLeft=bay.mullionX+.019,sashBottom=bay.transomY+.029,sashTop=top-.020;
  const sw=hingeX-sashLeft,sh=sashTop-sashBottom;
  // +Z faces the room. The right-hand hinge opens the free left edge inward.
  // A restrained angle leaves clearance behind the drying rail across the reveal.
  sash.position.set(hingeX,(sashTop+sashBottom)/2,z+.060);sash.rotation.y=.12;root.add(sash);
  for(const x of [-sw,0])box(.040,sh,.044,frameMat,x,0,0,sash,.003);
  for(const y of [-sh/2,sh/2])box(sw+.04,.040,.044,frameMat,-sw/2,y,0,sash,.003);
  box(sw-.045,sh-.045,.008,M.glass,-sw/2,0,0,sash);
  box(.018,.115,.024,M.trim,-sw+.024,-.02,.034,sash,.006);
  for(const y of [-sh*.32,sh*.32])box(.025,.065,.037,frameMat,.015,y,.014,sash,.006);

  // Six intermediate rods only behind the upper-right casement. Their ends
  // recess into the opening, without exposed sockets or any freestanding posts.
  const grille=new THREE.Group();grille.name='connected-window-security-grille';root.add(grille);
  for(const y of [1.33,1.49,1.65,1.81,1.97,2.13]){
    const bar=rod([bay.mullionX-.012,y,z-.042],[right+.012,y,z-.042],.008,M.metal,grille);bar.name='grille-welded-crossbar';
  }

  // Leave the reveal clear: an empty telescopic drying rail is in the photograph.
  const railZ=bay.roomZ-.205,railY=2.13;
  const rail=rod([bay.left+.018,railY,railZ],[bay.right-.018,railY,railZ],.011,M.white,root);rail.name='empty-bay-drying-rail';
  for(const x of [bay.left+.014,bay.right-.014]){
    const cap=cylinder(.026,.026,.022,M.white,x,railY,railZ,root);cap.rotation.z=Math.PI/2;
  }
  return {sill,sash,grille};
}
