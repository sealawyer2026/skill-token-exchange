const hre = require("hardhat");

async function main() {
  console.log("Deploying TokenExchange contract...");
  
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  
  const TokenExchange = await hre.ethers.getContractFactory("TokenExchange");
  const tokenExchange = await TokenExchange.deploy();
  
  await tokenExchange.waitForDeployment();
  
  const address = await tokenExchange.getAddress();
  console.log("TokenExchange deployed to:", address);
  
  // 验证合约
  if (hre.network.name !== "hardhat" && hre.network.name !== "localhost") {
    console.log("Waiting for block confirmations...");
    await tokenExchange.deploymentTransaction().wait(5);
    
    await hre.run("verify:verify", {
      address: address,
      constructorArguments: []
    });
  }
  
  // 保存部署信息
  const fs = require("fs");
  const deploymentInfo = {
    network: hre.network.name,
    contract: "TokenExchange",
    address: address,
    deployer: deployer.address,
    timestamp: new Date().toISOString()
  };
  
  fs.writeFileSync(
    `deployment-${hre.network.name}.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );
  
  console.log("Deployment completed!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
