"""
Payload Generator untuk ISO 20022 Messages
"""
from faker import Faker
from datetime import datetime
import uuid
import hashlib

fake = Faker('id_ID')


def create_uuid():
    """Generate UUID without dashes (ISO 20022 compliant)"""
    return str(uuid.uuid4()).replace('-', '')


def generate_account_phone_id(account_id: str) -> str:
    """
    Generate consistent phone ID from account ID.
    This ensures fraud rules can correctly attribute alerts to specific accounts.
    
    Args:
        account_id: Account identifier
    
    Returns:
        Phone number format ID (e.g., +62812345678)
    """
    if not account_id:
        return "+62811111111"  # Default fallback
    
    # Create consistent hash from account_id
    hash_digest = hashlib.md5(account_id.encode()).hexdigest()
    # Convert first 9 hex chars to decimal and format as phone
    phone_suffix = int(hash_digest[:9], 16) % 1000000000
    return f"+62{phone_suffix:09d}"


def generate_pain001(debtor_account=None, amount=None, debtor_name=None, 
                     creditor_account=None, creditor_name=None, purpose="TRANSFER"):
    """
    Generate pain.001.001.11 - Customer Credit Transfer Initiation
    
    Use Case: Customer (Debtor) initiates a payment/transfer request
    Example: User clicks "Transfer" in mobile banking app
    
    Args:
        debtor_account: Debtor's account ID (sender)
        amount: Transaction amount
        debtor_name: Debtor's name
        creditor_account: Creditor's account ID (receiver)
        creditor_name: Creditor's name
        purpose: Transaction purpose (TRANSFER, BILL_PAYMENT, etc.)
    """
    message_id = create_uuid()
    end_to_end_id = create_uuid()
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    # Generate realistic data
    debtor_name_parts = (debtor_name or fake.name()).split()
    if len(debtor_name_parts) < 2: debtor_name_parts.append("User")
    
    creditor_name_parts = (creditor_name or fake.name()).split()
    if len(creditor_name_parts) < 2: creditor_name_parts.append("Merchant")
    
    debtor_id = "+27730975224"
    debtor_id_type = "TAZAMA_EID"
    debtor_account_id = debtor_account or "1234567890"
    debtor_account_id_type = "MSISDN"
    debtor_agent_id = "fsp001"
    
    creditor_id = "+27707650428"
    creditor_id_type = "TAZAMA_EID"
    creditor_account_id = creditor_account or "0987654321"
    creditor_account_id_type = "MSISDN"
    creditor_agent_id = "fsp002"
    
    transaction_amount = amount or float(round(fake.random.uniform(100, 10000), 2))
    debtor_dob = "1968-02-01"
    
    payload = {
        "TxTp": "pain.001.001.11",
        "CstmrCdtTrfInitn": {
            "GrpHdr": {
                "MsgId": message_id,
                "CreDtTm": timestamp,
                "NbOfTxs": 1,
                "InitgPty": {
                    "Nm": " ".join(debtor_name_parts),
                    "Id": {
                        "PrvtId": {
                            "DtAndPlcOfBirth": {
                                "BirthDt": debtor_dob,
                                "CityOfBirth": "Unknown",
                                "CtryOfBirth": "ZZ"
                            },
                            "Othr": [{
                                "Id": debtor_id,
                                "SchmeNm": {
                                    "Prtry": debtor_account_id_type
                                }
                            }]
                        }
                    },
                    "CtctDtls": {
                        "MobNb": debtor_id
                    }
                }
            },
            "PmtInf": {
                "PmtInfId": create_uuid(),
                "PmtMtd": "TRA",
                "ReqdAdvcTp": {
                    "DbtAdvc": {
                        "Cd": "ADWD",
                        "Prtry": "Advice with transaction details"
                    }
                },
                "ReqdExctnDt": {
                    "Dt": datetime.utcnow().strftime("%Y-%m-%d"),
                    "DtTm": timestamp
                },
                "Dbtr": {
                    "Nm": " ".join(debtor_name_parts),
                    "Id": {
                        "PrvtId": {
                            "DtAndPlcOfBirth": {
                                "BirthDt": debtor_dob,
                                "CityOfBirth": "Unknown",
                                "CtryOfBirth": "ZZ"
                            },
                            "Othr": [{
                                "Id": debtor_id,
                                "SchmeNm": {
                                    "Prtry": debtor_id_type
                                }
                            }]
                        }
                    },
                    "CtctDtls": {
                        "MobNb": debtor_id
                    }
                },
                "DbtrAcct": {
                    "Id": {
                        "Othr": [{
                            "Id": debtor_account_id,
                            "SchmeNm": {
                                "Prtry": debtor_account_id_type
                            }
                        }]
                    },
                    "Nm": " ".join(debtor_name_parts)
                },
                "DbtrAgt": {
                    "FinInstnId": {
                        "ClrSysMmbId": {
                            "MmbId": debtor_agent_id
                        }
                    }
                },
                "CdtTrfTxInf": {
                    "PmtId": {
                        "EndToEndId": end_to_end_id
                    },
                    "PmtTpInf": {
                        "CtgyPurp": {
                            "Prtry": purpose
                        }
                    },
                    "Amt": {
                        "InstdAmt": {
                            "Amt": {
                                "Amt": transaction_amount,
                                "Ccy": "IDR"
                            }
                        },
                        "EqvtAmt": {
                            "Amt": {
                                "Amt": transaction_amount,
                                "Ccy": "IDR"
                            },
                            "CcyOfTrf": "IDR"
                        }
                    },
                    "XchgRateInf": {
                        "UnitCcy": "IDR",
                        "XchgRate": 1.0
                    },
                    "ChrgBr": "DEBT",
                    "CdtrAgt": {
                        "FinInstnId": {
                            "ClrSysMmbId": {
                                "MmbId": creditor_agent_id
                            }
                        }
                    },
                    "Cdtr": {
                        "Nm": " ".join(creditor_name_parts),
                        "Id": {
                            "PrvtId": {
                                "DtAndPlcOfBirth": {
                                    "BirthDt": "1935-05-08",
                                    "CityOfBirth": "Unknown",
                                    "CtryOfBirth": "ZZ"
                                },
                                "Othr": [{
                                    "Id": creditor_id,
                                    "SchmeNm": {
                                        "Prtry": creditor_id_type
                                    }
                                }]
                            }
                        },
                        "CtctDtls": {
                            "MobNb": creditor_id
                        }
                    },
                    "CdtrAcct": {
                        "Id": {
                            "Othr": [{
                                "Id": creditor_account_id,
                                "SchmeNm": {
                                    "Prtry": creditor_account_id_type
                                }
                            }]
                        },
                        "Nm": " ".join(creditor_name_parts)
                    },
                    "Purp": {
                        "Cd": "MP2P"
                    },
                    "RgltryRptg": {
                        "Dtls": {
                            "Tp": "BALANCE OF PAYMENTS",
                            "Cd": "100"
                        }
                    },
                    "RmtInf": {
                        "Ustrd": f"Payment initiated by {' '.join(debtor_name_parts)}"
                    },
                    "SplmtryData": {
                        "Envlp": {
                            "Doc": {
                                "Dbtr": {
                                    "FrstNm": debtor_name_parts[0] if debtor_name_parts else "Unknown",
                                    "MddlNm": debtor_name_parts[1] if len(debtor_name_parts) > 1 else "",
                                    "LastNm": debtor_name_parts[-1] if len(debtor_name_parts) > 2 else "",
                                    "MrchntClssfctnCd": "BLANK"
                                },
                                "Cdtr": {
                                    "FrstNm": creditor_name_parts[0] if creditor_name_parts else "Unknown",
                                    "MddlNm": creditor_name_parts[1] if len(creditor_name_parts) > 1 else "",
                                    "LastNm": creditor_name_parts[-1] if len(creditor_name_parts) > 2 else "",
                                    "MrchntClssfctnCd": "BLANK"
                                },
                                "DbtrFinSvcsPrvdrFees": {
                                    "Ccy": "IDR",
                                    "Amt": 0.00
                                },
                                "Xprtn": (datetime.utcnow().replace(year=datetime.utcnow().year + 1)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                            }
                        }
                    }
                }
            },
            "SplmtryData": {
                "Envlp": {
                    "Doc": {
                        "InitgPty": {
                            "InitrTp": "CONSUMER",
                            "Glctn": {
                                "Lat": "-6.2088",
                                "Long": "106.8456"
                            }
                        }
                    }
                }
            }
        }
    }
    
    return payload, message_id, end_to_end_id


def generate_pain013(debtor_account=None, amount=None, debtor_name=None, 
                     creditor_account=None, creditor_name=None):
    """
    Generate pain.013.001.09 - Creditor Payment Activation Request
    
    Use Case: Creditor/Merchant requests payment from a customer
    Example: QR Payment, Bill Payment, Invoice Request
    
    Args:
        debtor_account: Debtor's account ID (payer)
        amount: Requested payment amount
        debtor_name: Debtor's name
        creditor_account: Creditor's account ID (payment requester)
        creditor_name: Creditor's name
    """
    message_id = create_uuid()
    end_to_end_id = create_uuid()
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    # Generate realistic data
    debtor_name_parts = (debtor_name or fake.name()).split()
    if len(debtor_name_parts) < 2: debtor_name_parts.append("User")
    
    creditor_name_parts = (creditor_name or fake.name()).split()
    if len(creditor_name_parts) < 2: creditor_name_parts.append("Merchant")
    
    debtor_id = "+27730975224"
    debtor_id_type = "TAZAMA_EID"
    debtor_account_id = debtor_account or "1234567890"
    debtor_account_id_type = "MSISDN"
    debtor_agent_id = "fsp001"
    
    creditor_id = "+27707650428"
    creditor_id_type = "TAZAMA_EID"
    creditor_account_id = creditor_account or "0987654321"
    creditor_account_id_type = "MSISDN"
    creditor_agent_id = "fsp002"
    
    transaction_amount = amount or float(round(fake.random.uniform(100, 10000), 2))
    debtor_dob = "1968-02-01"
    
    payload = {
        "TxTp": "pain.013.001.09",
        "CdtrPmtActvtnReq": {
            "GrpHdr": {
                "MsgId": message_id,
                "CreDtTm": timestamp,
                "NbOfTxs": 1,
                "InitgPty": {
                    "Nm": " ".join(creditor_name_parts),
                    "Id": {
                        "PrvtId": {
                            "DtAndPlcOfBirth": {
                                "BirthDt": "1935-05-08",
                                "CityOfBirth": "Unknown",
                                "CtryOfBirth": "ZZ"
                            },
                            "Othr": [{
                                "Id": creditor_id,
                                "SchmeNm": {
                                    "Prtry": creditor_account_id_type
                                }
                            }]
                        }
                    },
                    "CtctDtls": {
                        "MobNb": creditor_id
                    }
                }
            },
            "PmtInf": {
                "PmtInfId": create_uuid(),
                "PmtMtd": "TRA",
                "ReqdAdvcTp": {
                    "DbtAdvc": {
                        "Cd": "ADWD",
                        "Prtry": "Advice with transaction details"
                    }
                },
                "ReqdExctnDt": {
                    "DtTm": timestamp
                },
                "XpryDt": {
                    "DtTm": (datetime.utcnow().replace(year=datetime.utcnow().year + 1)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                },
                "Dbtr": {
                    "Nm": " ".join(debtor_name_parts),
                    "Id": {
                        "PrvtId": {
                            "DtAndPlcOfBirth": {
                                "BirthDt": debtor_dob,
                                "CityOfBirth": "Unknown",
                                "CtryOfBirth": "ZZ"
                            },
                            "Othr": [{
                                "Id": debtor_id,
                                "SchmeNm": {
                                    "Prtry": debtor_id_type
                                }
                            }]
                        }
                    },
                    "CtctDtls": {
                        "MobNb": debtor_id
                    }
                },
                "DbtrAcct": {
                    "Id": {
                        "Othr": [{
                            "Id": debtor_account_id,
                            "SchmeNm": {
                                "Prtry": debtor_account_id_type
                            }
                        }]
                    },
                    "Nm": " ".join(debtor_name_parts)
                },
                "DbtrAgt": {
                    "FinInstnId": {
                        "ClrSysMmbId": {
                            "MmbId": debtor_agent_id
                        }
                    }
                },
                "CdtTrfTxInf": {
                    "PmtId": {
                        "EndToEndId": end_to_end_id
                    },
                    "PmtTpInf": {
                        "CtgyPurp": {
                            "Prtry": "TRANSFER BLANK"
                        }
                    },
                    "Amt": {
                        "InstdAmt": {
                            "Amt": {
                                "Amt": transaction_amount,
                                "Ccy": "IDR"
                            }
                        },
                        "EqvtAmt": {
                            "Amt": {
                                "Amt": transaction_amount,
                                "Ccy": "IDR"
                            },
                            "CcyOfTrf": "IDR"
                        }
                    },
                    "ChrgBr": "DEBT",
                    "CdtrAgt": {
                        "FinInstnId": {
                            "ClrSysMmbId": {
                                "MmbId": creditor_agent_id
                            }
                        }
                    },
                    "Cdtr": {
                        "Nm": " ".join(creditor_name_parts),
                        "Id": {
                            "PrvtId": {
                                "DtAndPlcOfBirth": {
                                    "BirthDt": "1935-05-08",
                                    "CityOfBirth": "Unknown",
                                    "CtryOfBirth": "ZZ"
                                },
                                "Othr": [{
                                    "Id": creditor_id,
                                    "SchmeNm": {
                                        "Prtry": creditor_id_type
                                    }
                                }]
                            }
                        },
                        "CtctDtls": {
                            "MobNb": creditor_id
                        }
                    },
                    "CdtrAcct": {
                        "Id": {
                            "Othr": [{
                                "Id": creditor_account_id,
                                "SchmeNm": {
                                    "Prtry": creditor_account_id_type
                                }
                            }]
                        },
                        "Nm": " ".join(creditor_name_parts)
                    },
                    "Purp": {
                        "Cd": "MP2P"
                    },
                    "RgltryRptg": {
                        "Dtls": {
                            "Tp": "BALANCE OF PAYMENTS",
                            "Cd": "100"
                        }
                    },
                    "SplmtryData": {
                        "Envlp": {
                            "Doc": {
                                "PyeeRcvAmt": {
                                    "Amt": {
                                        "Amt": 0.00,
                                        "Ccy": "IDR"
                                    }
                                },
                                "PyeeFinSvcsPrvdrFee": {
                                    "Amt": {
                                        "Amt": 0.00,
                                        "Ccy": "IDR"
                                    }
                                },
                                "PyeeFinSvcsPrvdrComssn": {
                                    "Amt": {
                                        "Amt": 0.00,
                                        "Ccy": "IDR"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "SplmtryData": {
                "Envlp": {
                    "Doc": {
                        "InitgPty": {
                            "Glctn": {
                                "Lat": "-6.2088",
                                "Long": "106.8456"
                            }
                        }
                    }
                }
            }
        }
    }
    
    return payload, message_id, end_to_end_id


def generate_pacs008(debtor_account=None, amount=None, debtor_name=None, creditor_account=None, creditor_name=None):
    """
    Generate pacs.008 payment request matching Postman Collection structure (Tazama Compatible)
    
    IMPORTANT: Debtor ID is now dynamically generated from debtor_account.
    This ensures fraud rules correctly attribute alerts to the right account.
    """
    message_id = create_uuid()
    end_to_end_id = create_uuid()  # Postman uses uuid for E2E
    
    # Generate realistic data
    debtor_name_parts = (debtor_name or fake.name()).split()
    if len(debtor_name_parts) < 2: debtor_name_parts.append("User")
    
    creditor_name_parts = (creditor_name or fake.name()).split()
    if len(creditor_name_parts) < 2: creditor_name_parts.append("Merchant")

    # PHASE 2 FIX: Dynamic debtor_id based on account for correct attribution
    debtor_account_id = debtor_account or "1234567890"
    debtor_id = generate_account_phone_id(debtor_account_id)  # Dynamic, not hardcoded!
    debtor_id_type = "MSISDN"
    debtor_account_id_type = "MSISDN"  # Tazama maps this
    
    # PHASE 2 FIX: Dynamic creditor_id based on account
    creditor_account_id = creditor_account or "0987654321"
    creditor_id = generate_account_phone_id(creditor_account_id)  # Dynamic!
    creditor_id_type = "MSISDN"
    creditor_account_id_type = "MSISDN"

    transaction_amount = amount or float(round(fake.random.uniform(100, 10000), 2))
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    

    # REQUEST (ACTION): Financial Institution Customer Credit Transfer
    # Pesan ini adalah instruksi transfer uang (Example: A kirim ke B)
    # Structure based strictly on Postman Collection 'prepPacs008Msg'
    payload = {
        "TxTp": "pacs.008.001.10", # Required by Tazama Ingestion
        "FIToFICstmrCdtTrf": {
            "GrpHdr": {
                "MsgId": message_id,
                "CreDtTm": timestamp,
                "NbOfTxs": 1,
                "SttlmInf": {
                    "SttlmMtd": "CLRG"
                }
            },
            "CdtTrfTxInf": {
                "PmtId": {
                    "InstrId": "5ab4fc7355de4ef8a75b78b00a681ed2", # Magic ID from Postman
                    "EndToEndId": end_to_end_id
                },
                "IntrBkSttlmAmt": {
                    "Amt": {
                        "Amt": transaction_amount,
                        "Ccy": "IDR"
                    }
                },
                "InstdAmt": {
                    "Amt": {
                        "Amt": transaction_amount,
                        "Ccy": "IDR"
                    }
                },
                "XchgRate": 1.0,
                "ChrgBr": "DEBT",
                "ChrgsInf": {
                    "Amt": {
                        "Amt": 0.00,
                        "Ccy": "IDR"
                    },
                    "Agt": {
                        "FinInstnId": {
                            "ClrSysMmbId": {
                                "MmbId": "dfsp001" # Postman: debtorAgentId
                            }
                        }
                    }
                },
                "InitgPty": {
                    "Nm": " ".join(debtor_name_parts),
                    "Id": {
                        "PrvtId": {
                            "DtAndPlcOfBirth": {
                                "BirthDt": "1968-02-01",
                                "CityOfBirth": "Unknown",
                                "CtryOfBirth": "ZZ"
                            },
                             "Othr": [{
                                 "Id": debtor_id,
                                 "SchmeNm": {
                                     "Prtry": debtor_id_type
                                 }
                            }]
                        }
                    },
                    "CtctDtls": {
                        "MobNb": debtor_id
                    }
                },
                "Dbtr": {
                    "Nm": " ".join(debtor_name_parts),
                    "Id": {
                        "PrvtId": {
                             "DtAndPlcOfBirth": {
                                "BirthDt": "1968-02-01",
                                "CityOfBirth": "Unknown",
                                "CtryOfBirth": "ZZ"
                            },
                            "Othr": [{
                                "Id": debtor_id,
                                "SchmeNm": {
                                    "Prtry": debtor_id_type
                                }
                            }]
                        }
                    },
                    "CtctDtls": {
                        "MobNb": debtor_id
                    }
                },
                "DbtrAcct": {
                    "Id": {
                        "Othr": [{
                            "Id": debtor_account_id,
                            "SchmeNm": {
                                "Prtry": debtor_account_id_type
                            }
                        }]
                    },
                    "Nm": " ".join(debtor_name_parts)
                },
                "DbtrAgt": {
                    "FinInstnId": {
                        "ClrSysMmbId": {
                            "MmbId": "dfsp001"
                        }
                    }
                },
                "CdtrAgt": {
                    "FinInstnId": {
                        "ClrSysMmbId": {
                            "MmbId": "dfsp002" # Postman: creditorAgentId
                        }
                    }
                },
                "Cdtr": {
                    "Nm": " ".join(creditor_name_parts),
                    "Id": {
                        "PrvtId": {
                             "DtAndPlcOfBirth": {
                                "BirthDt": "1935-05-08",
                                "CityOfBirth": "Unknown",
                                "CtryOfBirth": "ZZ"
                            },
                            "Othr": [{
                                "Id": creditor_id,
                                "SchmeNm": {
                                    "Prtry": creditor_id_type
                                }
                            }]
                        }
                    },
                    "CtctDtls": {
                        "MobNb": creditor_id
                    }
                },
                "CdtrAcct": {
                    "Id": {
                        "Othr": [{
                            "Id": creditor_account_id,
                            "SchmeNm": {
                                "Prtry": creditor_account_id_type
                            }
                        }]
                    },
                    "Nm": " ".join(creditor_name_parts)
                },
                "Purp": {
                    "Cd": "MP2P"
                },
                "SplmtryData": {
                    "Envlp": {
                        "Doc": {
                            "Xprtn": (datetime.utcnow().replace(year=datetime.utcnow().year + 1)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                            "InitgPty": {
                                "Glctn": {
                                    "Lat": "-6.2088",
                                    "Long": "106.8456"
                                }
                            }
                        }
                    }
                }
            },
            "RgltryRptg": { # Moved outside CdtTrfTxInf
                "Dtls": {
                    "Tp": "BALANCE_OF_PAYMENTS",
                    "Cd": "100"
                }
            },
            "RmtInf": {
                "Ustrd": "Payment Transaction"
            },
            "SplmtryData": { # Outer SplmtryData also exists in Postman
                 "Envlp": {
                    "Doc": {
                        "Xprtn": (datetime.utcnow().replace(year=datetime.utcnow().year + 1)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                        "InitgPty": {
                            "InitrTp": "CONSUMER",
                            "Glctn": {
                                "Lat": "-6.2088",
                                "Long": "106.8456"
                            }
                        }
                    }
                }
            }
        }
    }
    
    return payload


def generate_pacs002(original_message_id, end_to_end_id, status_code="ACCC"):
    """
    Generate pacs.002 confirmation with correct ISO 20022 structure matching Postman
    """
    message_id = create_uuid()
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    # RESPONSE (RESULT): Payment Status Report
    # Pesan ini adalah konfirmasi status transfer (Sukses/Gagal)
    # Structure based on Postman 'prepPacs002Msg'
    payload = {
        "TxTp": "pacs.002.001.12",
        "FIToFIPmtSts": { # Note: Postman uses FIToFIPmtSts, not FIToFIPmtStsRpt
            "GrpHdr": {
                "MsgId": message_id,
                "CreDtTm": timestamp
            },
            "TxInfAndSts": {
                "OrgnlInstrId": original_message_id,
                "OrgnlEndToEndId": end_to_end_id,
                "TxSts": status_code,
                "ChrgsInf": [ # Postman has empty charges list
                    {
                        "Amt": { "Amt": 0.00, "Ccy": "USD" },
                        "Agt": { "FinInstnId": { "ClrSysMmbId": { "MmbId": "dfsp001" } } }
                    },
                    {
                        "Amt": { "Amt": 0.00, "Ccy": "USD" },
                        "Agt": { "FinInstnId": { "ClrSysMmbId": { "MmbId": "dfsp001" } } }
                    },
                     {
                        "Amt": { "Amt": 0.00, "Ccy": "USD" },
                        "Agt": { "FinInstnId": { "ClrSysMmbId": { "MmbId": "dfsp002" } } }
                    }
                ],
                "AccptncDtTm": timestamp,
                "InstgAgt": {
                    "FinInstnId": {
                        "ClrSysMmbId": {
                            "MmbId": "dfsp001"
                        }
                    }
                },
                "InstdAgt": {
                     "FinInstnId": {
                        "ClrSysMmbId": {
                            "MmbId": "dfsp002"
                        }
                    }
                }
            }
        }
    }

    # Add Reason Code for Rejection
    if status_code == "RJCT":
        payload["FIToFIPmtSts"]["TxInfAndSts"]["StsRsnInf"] = [{
            "Rsn": {
                "Prtry": "AC04"
            },
            "AddtlInf": ["Simulated Rejection: Account Closed"]
        }]
    
    return payload
