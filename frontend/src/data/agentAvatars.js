// Agent humanoid cyborg avatar URLs — mapped to American names
const AGENT_AVATARS = {
  "Sarah": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/4d686b82885d8f4f90f35055251245df4e68fbfb5f3c8b9fc5b6296511151a5a.png",
  "James": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/88cfe39c6a5319218155267be07401ca74245e2076c5805a10e5c4aa82e5da90.png",
  "Emily": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/7cf1f980e31d97ccb986f55c090c7303614a2952d6ca744b7ef14418e2ba6a4a.png",
  "Ryan": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/74e9c6d4e04d7689a97a4116f0950497846f7d61b625a5be81781b373ea73ebe.png",
  "Olivia": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/96071ecfa1198dc6225653b5d1616310560290e88caa19ed9179ad9995c9b785.png",
  "Emma": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/8cc0d4915addd9573febdf858232d229fbcf269c59192f73d1b494bb502e8e00.png",
  "Daniel": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/90e716ab9bf4aac802a8aadb5cecfc9c557431de79aea6b25bef229eb03f731b.png",
  "Madison": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/9e9d3a7ce3ef4e906ecf1703df595f0b754386ed19239b850ce64c35748f26ac.png",
  "Michael": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/39783208d3f3619aa87a9e9aece2799a3ad5fa86928cf89ac09a5612234c6897.png",
  "Ashley": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/88cedb34badd97318e757a2c09df919d96980a52c610b6773f5e8d0cccd4c2f0.png",
  "Carlos": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/3f76d9a72b1b7c775b44da50a077ee6f03cdbb1232efcfd607bfabc6eb3185af.png",
  "Nicole": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/db453614cba20fc7a5351421d953fdc11e0a5844a0d28e1a41fa46a0db55b667.png",
  "Tyler": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/4ff65571aac826e1ef60da2f7335c9f9e73c88fc50bcaa3795bde816448fe7bf.png",
  "Jessica": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/f6b02bb83a0148dea715e1cc24ccf321558653496fcf474231b4cfce34619163.png",
  "Marcus": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/fdb7fdd7ee1331b754a2052b67ea6e966bf322f5875639527ac8b59175e51266.png",
  "Chloe": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/bb27d9dcd52876c239cf9f2a5abb972977f633ee504eedfc2bc2bad0b631d902.png",
  "Kevin": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/e7ba28e326ce0717cff0ea28b6f01d385715074459e1d1fa5beb6000be7bb1c3.png",
  "Sophia": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/7f7b2e7ab2562fa5619f6e4f6546512e49d14080b6600d8874ae7ab6c99d109a.png",
  "Ethan": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/3a1e35ef8f596b2245d29a95a84b8cc21648b39f30034a79a91397cb9546a3f6.png",
  "Jasmine": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/2728e3d0b831541d1d3f4c3df6e23122c70346c2342f02be50cb7cb8f7ec27a7.png",
  "David": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/c0523a726341278785f2d00125b0e75f654b311388888e03e25a003eb334011c.png",
  "Megan": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/ae9eb10335a10bc30404a94fd223647e455fba5a4cb9c486c7b2f12edc1f202e.png",
  "Alex": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/7ee5c6d0536e613daa414ee2eb2fc4744e94b22c951fda3842aaaf6ad0cd819c.png",
  "Luna": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/aca1ab2f84d6538905a37ca012b4d26a9d3398ec2d3d2e1b31d43e1dcd7086b0.png",
  "Max": "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/3cb80343d2f21c1d23049cae9e70e862f849a2917ed89fd32992764ae19a3e98.png",
};

// Default avatar for AI-generated agents
export const DEFAULT_AVATAR = "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/7ee5c6d0536e613daa414ee2eb2fc4744e94b22c951fda3842aaaf6ad0cd819c.png";

export function getAgentAvatar(name) {
  return AGENT_AVATARS[name] || null;
}

export default AGENT_AVATARS;
