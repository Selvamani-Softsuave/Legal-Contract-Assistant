"""
Enums for Week 7 Practical: Agent Loops vs Fixed Workflows (Track F - Legal Contracts).
Provides strict typing for contract versioning, clause categorization, and budget monitors.
"""

from enum import Enum


class ContractVersionEnum(str, Enum):
    """
    Strictly typed contract version identifier for multi-version amendment tracking.
    """
    ORIGINAL = "ORIGINAL"
    AMENDMENT_V1 = "AMENDMENT_V1"
    AMENDMENT_V2 = "AMENDMENT_V2"
    FINAL_EXECUTED = "FINAL_EXECUTED"


class ClauseTypeEnum(str, Enum):
    """
    Standard legal clause classification types.
    """
    TERMINATION = "TERMINATION"
    NOTICE = "NOTICE"
    DEFINITIONS = "DEFINITIONS"
    GOVERNING_LAW = "GOVERNING_LAW"
    LIMITATION_OF_LIABILITY = "LIMITATION_OF_LIABILITY"
    PAYMENT_TERMS = "PAYMENT_TERMS"
    CONFIDENTIALITY = "CONFIDENTIALITY"
    EFFECTIVE_DATE = "EFFECTIVE_DATE"


class BudgetExceededReason(str, Enum):
    """
    Enumerated causes for clean budget-triggered loop termination.
    """
    MAX_ITERATIONS = "MAX_ITERATIONS"
    MAX_TOKENS = "MAX_TOKENS"
    MAX_COST = "MAX_COST"
    WALL_CLOCK_TIMEOUT = "WALL_CLOCK_TIMEOUT"
