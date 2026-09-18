import {addToilet} from './toilet.js?v=blender18';
import {addEntranceDetails} from './entrance-details.js?v=blender18';
import {plan} from './room-layout.js?v=blender18';
import {addShowerFixture} from './shower-fixture.js?v=blender18';

export function addBathroom(c){
  const {THREE,world,M,mat,box,cylinder,ellipsoid,rod,path,obstacle,cutaway,ceilings}=c;
  const bath=new THREE.Group();bath.position.y=plan.bath.floor;world.add(bath);
  const ceramic=mat('#f6f5ef',.20),chrome=mat('#b8c4c5',.20,{metalness:.94});
  const blue=mat('#a2b9bd',.55),inset=mat('#dfe8e6',.75),mirror=mat('#c0d5d6',.14,{metalness:.9});
  // Looking in from the passage: basin first on the left, toilet beyond, washer last.
  const sinkX=-.065,sinkZ=2.94;
  box(.49,.54,.36,blue,sinkX,.40,sinkZ,bath,.012);
  for(const x of [sinkX-.21,sinkX+.21])for(const z of [2.80,3.085])box(.037,.22,.037,blue,x,.14,z,bath,.004);
  for(const x of [sinkX-.12,sinkX+.12]){
    box(.232,.48,.024,M.white,x,.415,2.749,bath,.007);
    box(.173,.38,.009,inset,x,.415,2.731,bath,.006);
    box(.023,.03,.028,M.dark,x+(x<sinkX?.085:-.085),.45,2.713,bath,.003);
  }
  // Continuous inner bowl, rim and outside underside. No solid plane fills the cavity.
  const profile=[[0,.685],[.04,.685],[.09,.690],[.14,.704],[.185,.731],[.215,.767],[.231,.794],[.239,.806],[.251,.810],[.266,.804],[.278,.790],[.271,.764],[.250,.727],[.217,.696],[.164,.674],[.09,.664],[0,.664]];
  const bowlCurve=new THREE.SplineCurve(profile.reverse().map(([r,y])=>new THREE.Vector2(r,y)));
  const basin=new THREE.Mesh(new THREE.LatheGeometry(bowlCurve.getPoints(96),96),ceramic);
  basin.name='concave-washbasin';basin.scale.z=.79;basin.position.set(sinkX,0,2.903);basin.castShadow=basin.receiveShadow=true;bath.add(basin);
  box(.52,.024,.074,ceramic,sinkX,.793,3.088,bath,.01);
  cylinder(.019,.019,.002,chrome,sinkX,.687,2.903,bath,32);
  cylinder(.012,.012,.002,mat('#333d3e',.42),sinkX,.6883,2.903,bath,24);
  for(let i=0;i<6;i++){const a=i*Math.PI/3;cylinder(.0018,.0018,.001,chrome,sinkX+Math.cos(a)*.008,.6895,2.903+Math.sin(a)*.008,bath,6);}
  const faucet=new THREE.Group();faucet.name='clickable-faucet';faucet.userData.interactive='faucet';bath.add(faucet);
  rod([sinkX,.805,3.08],[sinkX,.956,3.08],.016,chrome,faucet);
  path([[sinkX,.954,3.08],[sinkX,.955,3.005],[sinkX,.92,2.986]],.014,chrome,faucet);
  box(.028,.010,.061,chrome,sinkX,.971,3.064,faucet,.004);
  // Pale blue cabinet, white framed mirror, three open shelves on the far side.
  box(.64,.79,.115,blue,-.075,1.49,3.105,bath,.008);
  box(.65,.033,.16,blue,-.075,1.905,3.088,bath,.007);
  box(.427,.695,.028,M.trim,.023,1.50,3.033,bath,.006);
  box(.365,.625,.008,mirror,.023,1.50,3.014,bath);
  for(const y of [1.10,1.34,1.60,1.87])box(.18,.021,.13,blue,-.30,y,3.082,bath);
  box(.013,.79,.13,blue,-.405,1.49,3.085,bath);
  rod([-.395,1.031,3.033],[.23,1.031,3.033],.010,chrome,bath);
  for(const x of [-.393,.23])rod([x,1.03,3.034],[x,1.03,3.10],.01,chrome,bath);
  const teal=mat('#33bac5',.37),lilac=mat('#c4619d',.46);
  cylinder(.030,.027,.18,teal,-.32,1.70,3.065,bath);
  cylinder(.029,.028,.17,M.white,-.25,1.696,3.065,bath);
  cylinder(.03,.023,.19,M.white,-.22,2.018,3.07,bath);
  cylinder(.03,.03,.05,lilac,-.22,2.003,3.07,bath);
  rod([-.22,2.10,3.07],[-.22,2.155,3.07],.006,M.white,bath);
  box(.071,.010,.028,M.white,-.204,2.158,3.07,bath,.004);
  cylinder(.036,.031,.105,M.white,.12,1.977,3.07,bath);
  box(.13,.025,.035,M.white,-.31,1.13,3.035,bath,.008);
  obstacle(-.33,.22,2.69,3.17);
  // Toilet faces across the narrow room towards the shower wall.
  addToilet(c,bath);
  obstacle(-.89,-.49,2.43,3.06);
  // Washer visible in the occupied-room reference, beyond the toilet on the left.
  box(.44,.82,.46,M.white,-1.155,.42,2.89,bath,.021);
  box(.421,.036,.424,M.dark,-1.155,.851,2.89,bath,.025);
  box(.27,.003,.30,mat('#344044',.2),-1.155,.872,2.90,bath,.012);
  box(.13,.032,.018,M.white,-1.155,.66,2.650,bath,.004);
  obstacle(-1.39,-.92,2.65,3.14);
  addShowerFixture(c,bath);
  for(const y of [.09,.16])path([[-1.37,y,3.15],[-1.37,y,1.95],[.19,y,1.95]],.013,M.white,bath);
  path([[-1.365,.12,3.13],[-1.365,1.10,3.13],[-1.365,1.13,3.07]],.013,M.white,bath);
  box(.045,.20,.045,M.white,-1.365,1.25,3.10,bath);
  box(.12,.006,.12,chrome,-.66,.014,2.32,bath);
  cylinder(.037,.037,.003,M.dark,-.66,.019,2.32,bath);
  for(let i=0;i<5;i++)box(.073,.003,.004,chrome,-.66,.022,2.29+i*.015,bath);
  // Door hinge is on the bedroom side. The door folds inside against the right wall.
  const door=new THREE.Group();door.position.set(.23,.085,1.995);door.rotation.y=Math.PI;door.name='open-bathroom-door';world.add(door);cutaway.push(door);
  box(.965,2.13,.026,mat('#a8c4c2',.55,{transparent:true,opacity:.46}),.4825,1.065,0,door);
  for(const x of [0,.965])box(.035,2.17,.055,M.white,x,1.085,0,door);
  for(const y of [.017,.70,1.42,2.15])box(.965,.026,.05,M.white,.4825,y,0,door);
  box(.021,2.13,.021,M.white,.50,1.065,0,door);
  box(.045,.21,.02,M.brass,.85,.99,-.042,door,.003);
  rod([.85,1.06,-.073],[.71,1.06,-.073],.008,M.brass,door);
  obstacle(-.74,.24,1.963,2.027);
  // Rectangular illuminated heater/light unit in the white slatted ceiling.
  ceilings.push(box(.62,.035,.275,M.white,-.49,2.422,2.51,bath,.008));
  ceilings.push(box(.38,.011,.226,mat('#f6fff9',.3,{emissive:'#eafff8',emissiveIntensity:1.1}),-.49,2.399,2.51,bath,.006));
  for(const x of [-.745,-.245])for(let z=2.414;z<2.62;z+=.019)ceilings.push(box(.08,.013,.006,M.metal,x,2.399,z,bath));
  // Side-wall door. The hinge touches the far corner, with the handle towards the bedroom.
  const woodDoor=new THREE.Group();woodDoor.name='entrance-door';woodDoor.position.set(plan.entry.x,0,plan.entry.hingeZ);woodDoor.rotation.y=-Math.PI/2;woodDoor.scale.z=-1;world.add(woodDoor);cutaway.push(woodDoor);
  box(.89,2.16,.044,M.doorWood,-.445,1.08,0,woodDoor,.01);
  for(const y of [.22,1.08,1.96])cylinder(.012,.012,.105,chrome,-.006,y,-.027,woodDoor,12);
  for(const x of [-.67,-.22])for(const y of [.40,1.11,1.78]){
    box(.335,.48,.015,M.doorWood,x,y,-.029,woodDoor,.015);
    for(const xx of [x-.18,x+.18])box(.02,.52,.025,M.doorWood,xx,y,-.043,woodDoor);
    for(const yy of [y-.26,y+.26])box(.38,.02,.025,M.doorWood,x,yy,-.043,woodDoor);
  }
  addEntranceDetails(c,woodDoor);
}
