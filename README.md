# OciVisuNet
## Introduction
I wrote this script to generate a graphical representation of Oracle Cloud Infrastructure (OCI) Virtual Cloud Network (VCN) with its different components including subnets, virtual machine instances, Internet gateways and Dynamic routing gateways. The following picture shows a sample of the script output:

![alt text](Figure_1-1.png "Description goes here")

## Requirements and usage:
To use this script you need to:

1. install and configure OCI Cli by following the instructions in this link:

[To install OCI CLI](https://github.com/oracle/oci-cli)

[To configure OCI CLI](https://docs.us-phoenix-1.oraclecloud.com/Content/API/SDKDocs/cliconfigure.htm)

2. Install the following python packages:
```
pip install networkx

pip install matplotlib
```

3. Confiure you VCN and Compartment OCID under the [config.py](https://github.com/aabujoda/OciVisuNet/blob/master/config.py) file

4. Run the script with:

```
python visuNet.py
```

