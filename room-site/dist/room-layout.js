// Plan coordinates in metres. Topology is confirmed by the owner and entrance photos;
// numerical dimensions remain proportional estimates until measured.
export const plan = {
  room: {x1:-1.4,x2:1.4,z1:-1.8,z2:3.18},
  bath: {x1:-1.4,x2:.25,z1:1.80,z2:3.18,floor:.085},
  bathDoor: {x:.29,z:2.43,width:1.06},
  // Facing back from the bedroom: the door is on the left side wall.
  entry: {x:1.40,z:2.67,width:.92,hingeZ:3.13},
};
// The deep bay is outside the room's front wall. Dimensions are photo estimates.
// Cabinet doors sit just in front of its left return; glazing belongs at the rear.
export const bayWindow = {
  left:-.86,right:1.08,bottom:.64,top:2.30,
  roomZ:-1.80,backZ:-2.40,frameZ:-2.30,sillFrontZ:-1.745,
  mullionX:.16,transomY:1.17,
};
export function floorHeight(x,z){return x<.30&&z>1.8?plan.bath.floor:0;}
// A 5 cm wide navigation body keeps narrow gaps usable, while walls stay solid.
export function canOccupy(x,z,colliders,radius=.025){
  const r=plan.room;
  if(x<=r.x1+radius||x>=r.x2-radius||z<=r.z1+radius||z>=r.z2-radius)return false;
  return !colliders.some(o=>x>o.x1-radius&&x<o.x2+radius&&z>o.z1-radius&&z<o.z2+radius);
}
export function buildArchitecture(c){
  const {THREE,world,M,box,wall,obstacle,cutaway,ceilings}=c;
  const {bath,entry}=plan;
  box(2.98,.14,5.16,M.white,0,-.085,.69);
  const tiles=(x0,x1,z0,z1,size,material,y)=>{
    for(let x=x0;x<x1-.001;x+=size)for(let z=z0;z<z1-.001;z+=size){
      const w=Math.min(size,x1-x),d=Math.min(size,z1-z);
      box(w-.002,.022,d-.002,material,x+w/2,y,z+d/2);
    }
  };
  tiles(-1.4,1.4,-1.8,1.8,.6,M.tile,0);
  tiles(.25,1.4,1.8,3.18,.6,M.tile,0);
  box(1.65,.085,1.38,M.white,-.575,.033,2.49);
  tiles(-1.4,.25,1.8,3.18,.30,M.bathTile,bath.floor);
  wall(.14,2.65,4.98,M.gray,-1.47,1.325,.69);
  const doorNear=entry.z-entry.width/2,doorFar=entry.hingeZ;
  wall(.14,2.65,doorNear+1.8,M.pink,1.47,1.325,(doorNear-1.8)/2,true);
  wall(.14,2.65,3.18-doorFar,M.pink,1.47,1.325,(3.18+doorFar)/2,true);
  // Lintel starts above the timber head jamb, never in the door opening.
  cutaway.push(box(.14,.40,entry.width,M.pink,1.47,2.45,entry.z));
  const bay=bayWindow,bayWidth=bay.right-bay.left,bayX=(bay.left+bay.right)/2;
  const bayDepth=bay.roomZ-bay.backZ,bayZ=(bay.roomZ+bay.backZ)/2;
  const leftReturn=wall(bay.left+1.4,2.65,bayDepth,M.pink,(-1.4+bay.left)/2,1.325,bayZ);leftReturn.name='bay-left-wall-return';
  const rightReturn=wall(1.4-bay.right,2.65,bayDepth,M.pink,(1.4+bay.right)/2,1.325,bayZ);rightReturn.name='bay-right-wall-return';
  const apron=box(bayWidth,bay.bottom,bayDepth,M.pink,bayX,bay.bottom/2,bayZ);apron.name='bay-window-solid-apron';
  const soffit=box(bayWidth,2.65-bay.top,bayDepth,M.pink,bayX,(2.65+bay.top)/2,bayZ);soffit.name='bay-window-recessed-soffit';
  obstacle(-1.4,1.4,bay.backZ,bay.roomZ);
  // The bathroom is a box behind the headboard, not a room beyond a cross-corridor.
  wall(1.72,2.65,.10,M.white,-.54,1.325,1.83,true);
  cutaway.push(box(1.65,2.47,.018,M.marble,-.575,1.32,1.89));
  // Bathroom's east wall carries its door, which opens towards the shower wall.
  wall(.10,2.65,.10,M.white,.30,1.325,1.93,true);
  wall(.10,2.65,.14,M.white,.30,1.325,3.10,true);
  cutaway.push(box(.10,.42,1.14,M.white,.30,2.44,2.48));
  const bframe=new THREE.Group();world.add(bframe);cutaway.push(bframe);
  for(const z of [1.96,3.03])box(.15,2.22,.047,M.trim,.30,1.20,z,bframe);
  box(.15,.057,1.13,M.trim,.30,2.285,2.495,bframe);
  box(.17,.08,1.06,M.white,.30,.055,2.495,bframe);
  // Solid end wall; entry is on the side, hinged at the rear corner.
  wall(2.8,2.65,.14,M.pink,0,1.325,3.25,true);
  for(const z of [doorNear,doorFar])cutaway.push(box(.17,2.23,.06,M.doorWood,entry.x,1.115,z));
  cutaway.push(box(.17,.065,1.02,M.doorWood,entry.x,2.24,entry.z));
  const jamb=box(.20,.126,.94,M.doorWood,1.445,2.207,entry.z);jamb.name='continuous-timber-head-jamb';cutaway.push(jamb);
  cutaway.push(box(.028,.046,.94,M.doorWood,1.360,2.159,entry.z));
  // Tile surfaces and joints in the wet room, raised floor and lower panel ceiling.
  box(.016,2.47,1.28,M.marble,-1.388,1.32,2.51);
  cutaway.push(box(1.65,2.47,.018,M.marble,-.575,1.32,3.171));
  for(let x=-1.4;x<.25;x+=.30){box(.002,2.42,.006,M.grout,x,1.32,1.903);cutaway.push(box(.002,2.42,.006,M.grout,x,1.32,3.157));}
  for(let y=.685;y<2.5;y+=.60){box(1.65,.002,.005,M.grout,-.575,y,1.902);cutaway.push(box(1.65,.002,.005,M.grout,-.575,y,3.156));box(.004,.002,1.27,M.grout,-1.377,y,2.525);}
  ceilings.push(box(2.8,.10,4.98,M.ceiling,0,2.70,.69));
  ceilings.push(box(1.67,.04,1.38,M.trim,-.575,2.54,2.49));
  for(let x=-1.38;x<.28;x+=.15)ceilings.push(box(.002,.003,1.36,M.grout,x,2.516,2.49));
  // Continuous room trim plus the plain white face behind the bed.
  for(const y of [2.48,2.53,2.57,2.61]){const d=(y-2.4)*.32;box(2.8,.036,d,M.trim,0,y,-1.8+d/2);box(d,.036,3.6,M.trim,-1.4+d/2,y,0);cutaway.push(box(d,.036,4.98,M.trim,1.4-d/2,y,.69));}
  box(.027,.085,3.6,M.black,-1.383,.055,0);
  cutaway.push(box(.027,.085,doorNear+1.8,M.black,1.383,.055,(doorNear-1.8)/2));
  cutaway.push(box(2.8,.085,.027,M.black,0,.055,3.166));
  box(2.8,.085,.027,M.black,0,.055,-1.783);
  cutaway.push(box(1.72,.085,.025,M.black,-.54,.055,1.77));
  cutaway.push(box(1.72,.035,.06,M.trim,-.54,2.615,1.77));
}
