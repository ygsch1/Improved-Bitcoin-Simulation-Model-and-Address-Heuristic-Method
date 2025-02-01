# Improved-Address-Clustering-Heuristic-and-Bitcoin-Blockchain-Investigation

## Bitcoin Transaction Simulation Model

This repository contains the code and documentation for an enhanced simulation model designed to accurately replicate real-world Bitcoin transactions. This model is intended for research purposes, particularly in the areas of blockchain analysis and crypto forensics. It is an improved version based on real-world blockchain data investigations.

## Overview

The absence of ground truth data introduces uncertainty into the results of existing address clustering techniques, hindering the reliability of findings. This project addresses the challenges posed by the inherent limitations of the Bitcoin blockchain and the increasing adoption of privacy-enhancing technologies, which can lead to uncertain performance of address clustering algorithms. To mitigate these issues, we have developed a simulation model with a detailed transaction structure, allowing for the evaluation of clustering techniques based on internal transaction parameters.

## Key Features

*   **Realistic Bitcoin Transaction Simulation:** The model simulates Bitcoin transactions with configurable parameters, including:
    *   Number of nodes in the simulated network
    *   Total volume of transactions generated
    *   Transaction version number, sequence number, lock time, and Segregated Witness (SegWit) flag
    *   Distribution of input and output counts
    *   Distribution of transaction types (consolidation, transfer, complex, multiple payments)
    *   Distribution of address types (P2PKH, P2SH, P2WPKH, P2WSH, P2TR)
*   **Evaluation Framework:** A framework for evaluating address clustering algorithms, including:
    *   Clustering algorithm implementation (based on internal transaction parameters)
    *   Performance evaluation (calculation of error rates)

## Model Description

In the simulator, each node is a fully functional Bitcoin node with the following essential components: wallet, storage, routing, and consensus mechanisms. The simulation data is stored at the end of the simulation.

## Instructions for Use

### Prerequisites

Before running the simulation, ensure you have the following installed:

*   Python 3.7 or higher
*   Required Python libraries

### Parameter Configuration

The model allows for setting the number of nodes and the total transaction volume in the simulated network. Additionally, users can configure their own parameters within the transaction structure to simulate Bitcoin transactions. The initial settings for internal transaction parameters of the model are based on the statistical patterns observed in real-world Bitcoin blockchain data (block height: 0-823785).

### Run Command

To run the simulator, execute `main.py`. After the simulation is complete, you can optionally run `add_timestamp.py` to add timestamps to each transaction record in `Transaction.log`. These timestamps are derived from the block times in `Block.csv`.

### Simulation Outcomes

Following the simulation, the results are saved in the following five files:

*   **`Simulation.log`:** This log file records all activity information of the simulator during the entire simulation process. The log includes information about Bitcoin nodes ("peer") and their unique identifiers ("pid").
*   **`Wallet.log`:** This file contains wallet-related information for each node, including confirmed UTXOs, address lists, and balances. Each UTXO record includes the Bitcoin amount, relevant pointer, address, address type, and index position in the original transaction.
*   **`Transaction.log`:** This file stores transactions from all blocks, recording each transaction structure. The transaction format follows real Bitcoin transactions' JavaScript Object Notation (JSON) structure. 
*   **`Block.csv`:** The CSV file saves all generated block information within the simulated network, including block hash, timestamp, the ID of transactions in the block, and details related to coinbase transactions. The genesis block is located at the beginning of this file.
*   **`Addr_type.csv`:** It keeps all Bitcoin addresses and corresponding address types within the simulated network. Address type labels can also be extracted by parsing the transaction structure in Transaction.log. This file is generated to facilitate any query needs.

Sample results can be found in the /example_data directory. More details about the simulation model can be found in the paper: Improved Address Clustering Heuristic and Bitcoin Blockchain Investigation.


