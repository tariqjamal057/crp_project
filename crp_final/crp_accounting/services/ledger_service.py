# crp_accounting/services/ledger_service.py

import logging
from decimal import Decimal
from datetime import date
from typing import List, Dict, Optional, Union, NamedTuple

from django.db import models  # For output_field in Coalesce
from django.db.models import Sum, Q, Prefetch
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.conf import settings

# --- Model Imports ---
<<<<<<< HEAD
from ..models.journal import Voucher, VoucherLine, DrCrType, TransactionStatus
from ..models.coa import Account
# from ..models.party import Party # Only if voucher.party is directly used in ledger line construction
from crp_core.enums import AccountNature

# --- Company Import ---
try:
    from company.models import Company
except ImportError:
    Company = None
=======
# Ensure these paths are correct for your project structure
from ..models.journal import Voucher, VoucherLine, DrCrType, TransactionStatus
from ..models.coa import Account
# from ..models.party import Party # Uncomment if directly used for particulars
from crp_core.enums import AccountNature  # Assuming crp_core is an app at the same level or in PYTHONPATH

# --- Company Import ---
try:
    from company.models import Company  # Adjust if your company app has a different path
except ImportError:
    Company = None  # Handle if Company app is optional or not found
>>>>>>> 6bf6cecba810d211bb58ec8cdc516eeae683c30c

logger = logging.getLogger(__name__)

# --- Constants ---
<<<<<<< HEAD
CACHE_OPENING_BALANCE_TIMEOUT = getattr(settings, 'CACHE_OPENING_BALANCE_TIMEOUT', 900)
=======
CACHE_OPENING_BALANCE_TIMEOUT = getattr(settings, 'CACHE_OPENING_BALANCE_TIMEOUT', 900)  # Default 15 mins
>>>>>>> 6bf6cecba810d211bb58ec8cdc516eeae683c30c
ZERO_DECIMAL = Decimal('0.00')


# --- Helper Data Structure ---
class MinimalAccountForBalance(NamedTuple):
    pk: Union[int, str]
    account_nature: str


# =============================================================================
# Ledger Service Functions (Tenant Aware & Optimized)
# =============================================================================

def calculate_account_balance_upto(
        company_id: Union[int, str],
        account_for_balance: MinimalAccountForBalance,
        date_exclusive: Optional[date]
) -> Decimal:
    """
    Calculates the closing balance for an account within a specific company,
    based on all POSTED transactions strictly *before* a specified date.
    Includes caching.
    """
    if not date_exclusive:
        return ZERO_DECIMAL

    cache_key = f"acc_ob_{company_id}_{account_for_balance.pk}_{date_exclusive.isoformat()}"
    cached_balance = cache.get(cache_key)
    if cached_balance is not None:
<<<<<<< HEAD
=======
        # logger.debug(f"Cache HIT for opening balance: Key='{cache_key}'")
>>>>>>> 6bf6cecba810d211bb58ec8cdc516eeae683c30c
        return Decimal(cached_balance)

    logger.debug(
        f"Cache MISS for opening balance: Key='{cache_key}'. Calculating for Co {company_id}, Acc PK {account_for_balance.pk}...")

    lines = VoucherLine.objects.filter(
        account_id=account_for_balance.pk,
        voucher__company_id=company_id,
        voucher__status=TransactionStatus.POSTED.value,
        voucher__date__lt=date_exclusive
    )

    aggregation = lines.aggregate(
        total_debit=Coalesce(
            Sum('amount', filter=Q(dr_cr=DrCrType.DEBIT.value)),
            ZERO_DECIMAL, output_field=models.DecimalField()
        ),
        total_credit=Coalesce(
            Sum('amount', filter=Q(dr_cr=DrCrType.CREDIT.value)),
            ZERO_DECIMAL, output_field=models.DecimalField()
        )
    )
    debit_total = aggregation['total_debit']
    credit_total = aggregation['total_credit']

    balance = ZERO_DECIMAL
    if account_for_balance.account_nature == AccountNature.DEBIT.value:
        balance = debit_total - credit_total
    elif account_for_balance.account_nature == AccountNature.CREDIT.value:
        balance = credit_total - debit_total
    else:
        logger.error(
<<<<<<< HEAD
            f"Co {company_id}, Acc PK {account_for_balance.pk} has unexpected nature '{account_for_balance.account_nature}'.")
        raise ValueError(
            f"Invalid account nature '{account_for_balance.account_nature}' for account (PK: {account_for_balance.pk}).")
=======
            f"Co {company_id}, Acc PK {account_for_balance.pk} has unexpected nature '{account_for_balance.account_nature}'. Cannot calculate balance accurately."
        )
        raise ValueError(
            f"Invalid account nature '{account_for_balance.account_nature}' for account (PK: {account_for_balance.pk}). Cannot calculate balance."
        )
>>>>>>> 6bf6cecba810d211bb58ec8cdc516eeae683c30c

    try:
        cache.set(cache_key, str(balance), timeout=CACHE_OPENING_BALANCE_TIMEOUT)
    except Exception as e:
        logger.error(f"Failed to cache opening balance for Key='{cache_key}': {e}", exc_info=True)

    return balance


def get_account_ledger_data(
        company_id: Union[int, str],
        account_pk: Union[int, str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
) -> Dict[str, Union[Dict, Decimal, List[Dict], Optional[date]]]:
    """
    Retrieves detailed ledger transaction history for a specific account
    within a specific company and optional date range.
    """
    if not company_id:
        raise ValueError("company_id must be provided for ledger data retrieval.")
    if not account_pk:
        raise ValueError("account_pk must be provided for ledger data retrieval.")

    try:
        account_data_dict = Account.objects.values(
            'pk', 'account_number', 'account_name', 'account_nature', 'currency'
        ).get(
            pk=account_pk,
            company_id=company_id
        )
    except Account.DoesNotExist:
        logger.error(f"Ledger requested for Account ID {account_pk} not found in Company ID {company_id}")
        raise ObjectDoesNotExist(f"Account with ID {account_pk} not found in the specified company.")

    minimal_account = MinimalAccountForBalance(
        pk=account_data_dict['pk'],
        account_nature=account_data_dict['account_nature']
    )

    logger.info(
        f"Generating ledger for Co ID {company_id}, Acc: {account_data_dict['account_name']} ({account_pk}) | "
        f"Period: {start_date or 'Beginning'} to {end_date or 'End'}"
    )

    opening_balance = calculate_account_balance_upto(
        company_id=company_id,
        account_for_balance=minimal_account,
        date_exclusive=start_date
    )

<<<<<<< HEAD
=======
    # --- CORRECTED `select_related` ---
>>>>>>> 6bf6cecba810d211bb58ec8cdc516eeae683c30c
    ledger_lines_query = VoucherLine.objects.filter(
        account_id=account_pk,
        voucher__company_id=company_id,
        voucher__status=TransactionStatus.POSTED.value
<<<<<<< HEAD
    ).select_related('voucher').order_by('voucher__date', 'voucher__created_at', 'pk')
=======
    ).select_related(
        'voucher'  # Corrected: voucher_type is not relational here
    ).prefetch_related(
        Prefetch('voucher__lines', queryset=VoucherLine.objects.select_related('account'))
    ).order_by('voucher__date', 'voucher__created_at', 'pk')
    # --- END CORRECTION ---
>>>>>>> 6bf6cecba810d211bb58ec8cdc516eeae683c30c

    if start_date:
        ledger_lines_query = ledger_lines_query.filter(voucher__date__gte=start_date)
    if end_date:
        ledger_lines_query = ledger_lines_query.filter(voucher__date__lte=end_date)

    ledger_lines = list(ledger_lines_query)

    entries: List[Dict] = []
    running_balance: Decimal = opening_balance
    period_total_debit: Decimal = ZERO_DECIMAL
    period_total_credit: Decimal = ZERO_DECIMAL
    is_debit_nature_account: bool = (account_data_dict['account_nature'] == AccountNature.DEBIT.value)

    for line in ledger_lines:
        is_debit_line = line.dr_cr == DrCrType.DEBIT.value

        debit_amount = line.amount if is_debit_line else ZERO_DECIMAL
        credit_amount = line.amount if not is_debit_line else ZERO_DECIMAL

        balance_change: Decimal
        if is_debit_line:
            balance_change = debit_amount if is_debit_nature_account else -debit_amount
            period_total_debit += debit_amount
<<<<<<< HEAD
        else:  # is_credit_line
=======
        else:
>>>>>>> 6bf6cecba810d211bb58ec8cdc516eeae683c30c
            balance_change = -credit_amount if is_debit_nature_account else credit_amount
            period_total_credit += credit_amount

        running_balance += balance_change

<<<<<<< HEAD
=======
        # --- Determine Particulars (Contra Account Name) ---
        particulars_text = ""

        # Access prefetched lines for the current voucher.
        all_voucher_lines_for_this_voucher = list(line.voucher.lines.all())

        contra_accounts_names = []
        for v_line in all_voucher_lines_for_this_voucher:
            if v_line.pk != line.pk and v_line.account:  # Exclude the current line and ensure account exists
                contra_accounts_names.append(v_line.account.account_name)

        if contra_accounts_names:
            if len(contra_accounts_names) == 1:
                particulars_text = contra_accounts_names[0]
            else:
                # For multiple contra accounts, prioritize voucher narration, then line narration, then generic
                if line.voucher.narration:
                    particulars_text = line.voucher.narration
                elif line.narration:
                    particulars_text = line.narration
                else:
                    # You might want to join names if preferred:
                    # particulars_text = ", ".join(sorted(list(set(contra_accounts_names))))
                    particulars_text = _("Sundry Accounts")  # Or "As per details"
        else:
            # No contra-lines found (e.g. one-sided entry, data issue, or already handled by narration if it was set)
            # Fallback to voucher narration or line narration if particulars_text is still empty
            if not particulars_text:  # Check if it was already set by multi-account narration logic
                particulars_text = line.voucher.narration or line.narration or _(
                    "N/A")  # N/A or other appropriate default

        # Final fallback if particulars_text is still empty after all attempts
        if not particulars_text:
            particulars_text = _("Details not specified")
        # --- END Determine Particulars ---

>>>>>>> 6bf6cecba810d211bb58ec8cdc516eeae683c30c
        entries.append({
            'line_pk': line.pk,
            'date': line.voucher.date,
            'voucher_pk': line.voucher.pk,
            'voucher_number': line.voucher.voucher_number or f"V#{line.voucher.pk}",
<<<<<<< HEAD
            'voucher_type': line.voucher.get_voucher_type_display(),
            'narration': line.voucher.narration or line.narration or '',  # Combine narrations
            'reference': line.voucher.reference or '',
            'debit': debit_amount,
            'credit': credit_amount,
            'running_balance': running_balance
        })

    closing_balance = running_balance

    account_summary_for_response = {
        "id": account_data_dict['pk'],
        "account_number": account_data_dict['account_number'],
        "account_name": account_data_dict['account_name'],
        "currency": account_data_dict['currency'],
=======
            'voucher_type_display': line.voucher.get_voucher_type_display(),
            'particulars': particulars_text,
            'narration': line.voucher.narration or line.narration or '',
            'reference': line.voucher.reference or '',
            'debit': debit_amount,
            'credit': credit_amount,
            'running_balance_display': {
                'amount': running_balance,
                'dr_cr': 'Dr' if (running_balance > ZERO_DECIMAL and is_debit_nature_account) or \
                                 (running_balance < ZERO_DECIMAL and not is_debit_nature_account) else \
                    'Cr' if (running_balance < ZERO_DECIMAL and is_debit_nature_account) or \
                            (running_balance > ZERO_DECIMAL and not is_debit_nature_account) else \
                        '',  # Empty if zero balance or for unambiguous zero
                # Note: For credit nature accounts, a "positive" running_balance means Credit.
                # A "negative" running_balance (less than zero) for a credit nature account means it has a debit balance.
            }
        })

    closing_balance = running_balance
    closing_balance_dr_cr = 'Dr' if (closing_balance > ZERO_DECIMAL and is_debit_nature_account) or \
                                    (closing_balance < ZERO_DECIMAL and not is_debit_nature_account) else \
        'Cr' if (closing_balance < ZERO_DECIMAL and is_debit_nature_account) or \
                (closing_balance > ZERO_DECIMAL and not is_debit_nature_account) else \
            ''

    opening_balance_dr_cr = 'Dr' if (opening_balance > ZERO_DECIMAL and is_debit_nature_account) or \
                                    (opening_balance < ZERO_DECIMAL and not is_debit_nature_account) else \
        'Cr' if (opening_balance < ZERO_DECIMAL and is_debit_nature_account) or \
                (opening_balance > ZERO_DECIMAL and not is_debit_nature_account) else \
            ''

    account_summary_for_response = {
        "pk": account_data_dict['pk'],
        "account_number": account_data_dict['account_number'],
        "account_name": account_data_dict['account_name'],
        "currency": account_data_dict['currency'],
        "account_nature": account_data_dict['account_nature']
>>>>>>> 6bf6cecba810d211bb58ec8cdc516eeae683c30c
    }

    return {
        'account': account_summary_for_response,
        'start_date': start_date,
        'end_date': end_date,
<<<<<<< HEAD
        'opening_balance': opening_balance,
        'total_debit': period_total_debit,
        'total_credit': period_total_credit,
        'entries': entries,
        'closing_balance': closing_balance,
    }
# # crp_accounting/services/ledger_service.py
#
# import logging
# from decimal import Decimal
# from datetime import date, datetime
# from typing import List, Dict, Optional, Tuple, Union
#
# from django.db import models
# from django.db.models import Sum, Q, F, Case, When, Value, OuterRef, Subquery
# from django.db.models.functions import Coalesce
# from django.utils.translation import gettext_lazy as _
# from django.core.exceptions import ObjectDoesNotExist
# from django.core.cache import cache # Import Django's cache framework
# from django.conf import settings # To potentially make timeout configurable
#
# # --- Model Imports ---
# from ..models.journal import Voucher, VoucherLine, DrCrType, TransactionStatus
# from ..models.coa import Account
# from crp_core.enums import AccountNature
#
# logger = logging.getLogger(__name__)
#
# # --- Constants ---
# # Cache timeout for opening balance in seconds (e.g., 15 minutes).
# # Can be overridden in Django settings.py: CACHE_OPENING_BALANCE_TIMEOUT = 900
# CACHE_OPENING_BALANCE_TIMEOUT = getattr(settings, 'CACHE_OPENING_BALANCE_TIMEOUT', 900)
#
#
# # =============================================================================
# # Ledger Service Functions
# # =============================================================================
#
# def calculate_account_balance_upto(account: Account, date_exclusive: Optional[date]) -> Decimal:
#     """
#     Calculates the closing balance for an account based on all POSTED transactions
#     strictly *before* a specified date (exclusive).
#
#     Uses basic time-based caching to optimize repeated calculations for the same
#     account and date.
#
#     Args:
#         account: The Account instance.
#         date_exclusive: The date before which transactions should be considered.
#                         If None, the balance is 0.
#
#     Returns:
#         Decimal: The calculated balance before the specified date.
#
#     Raises:
#         ValueError: If the account's nature is misconfigured.
#     """
#     if not date_exclusive:
#         logger.debug(f"Calculating balance up to None for Account {account.pk}, returning 0.")
#         return Decimal('0.00')
#
#     # --- Caching Logic ---
#     # Generate a unique cache key based on account and date.
#     # Using ISO format ensures consistent date representation.
#     cache_key = f"acc_ob_{account.pk}_{date_exclusive.isoformat()}"
#     cached_balance = cache.get(cache_key)
#
#     if cached_balance is not None:
#         logger.debug(f"Cache HIT for opening balance: Key='{cache_key}', Account={account.pk}, Date={date_exclusive}")
#         # Ensure the cached value is returned as a Decimal
#         return Decimal(cached_balance)
#     # --- End Caching Logic ---
#
#     logger.debug(f"Cache MISS for opening balance: Key='{cache_key}', Account={account.pk}, Date={date_exclusive}. Calculating...")
#
#     # Fetch relevant lines if not found in cache
#     lines = VoucherLine.objects.filter(
#         account=account,
#         voucher__status=TransactionStatus.POSTED,
#         voucher__date__lt=date_exclusive
#     )
#
#     aggregation = lines.aggregate(
#         total_debit=Coalesce(
#             Sum('amount', filter=Q(dr_cr=DrCrType.DEBIT.name)),
#             Decimal('0.00'),
#             output_field=models.DecimalField()
#         ),
#         total_credit=Coalesce(
#             Sum('amount', filter=Q(dr_cr=DrCrType.CREDIT.name)),
#             Decimal('0.00'),
#             output_field=models.DecimalField()
#         )
#     )
#     debit_total = aggregation['total_debit']
#     credit_total = aggregation['total_credit']
#
#     # Calculate balance based on account nature
#     if account.account_nature == AccountNature.DEBIT.name:
#         balance = debit_total - credit_total
#     elif account.account_nature == AccountNature.CREDIT.name:
#         balance = credit_total - debit_total
#     else:
#         logger.error(f"Account {account} (PK: {account.pk}) has unexpected account nature '{account.account_nature}'.")
#         raise ValueError(f"Invalid account nature '{account.account_nature}' configured for account {account.account_number}.")
#
#     # --- Store calculated balance in cache ---
#     try:
#         # Store as string to avoid potential float precision issues with some backends,
#         # although Decimal should generally be fine with most modern backends.
#         # Converting back to Decimal on retrieval ensures type consistency.
#         cache.set(cache_key, str(balance), timeout=CACHE_OPENING_BALANCE_TIMEOUT)
#         logger.debug(f"Cached opening balance for Key='{cache_key}': {balance} (Timeout: {CACHE_OPENING_BALANCE_TIMEOUT}s)")
#     except Exception as e:
#         # Log caching errors but don't fail the main calculation
#         logger.error(f"Failed to cache opening balance for Key='{cache_key}': {e}", exc_info=True)
#     # --- End Store in Cache ---
#
#     logger.debug(f"Calculated balance up to {date_exclusive} for Account {account.pk}: {balance}")
#     return balance
#
#
# def get_account_ledger_data(
#     account_id: int,
#     start_date: Optional[date] = None,
#     end_date: Optional[date] = None
# ) -> Dict[str, Union[Account, Decimal, List[Dict], Optional[date]]]:
#     """
#     Retrieves detailed ledger transaction history for a specific account
#     within an optional date range. Leverages caching for opening balance calculation.
#
#     (Docstring remains the same as previous version regarding Args, Returns, Raises)
#     """
#     try:
#         account = Account.objects.select_related('account_group').get(pk=account_id)
#     except Account.DoesNotExist:
#         logger.error(f"Ledger requested for non-existent Account ID: {account_id}")
#         raise ObjectDoesNotExist(f"Account with ID {account_id} not found.")
#
#     logger.info(f"Generating ledger for Account: {account} ({account_id}) | Period: {start_date or 'Beginning'} to {end_date or 'End'}")
#
#     # --- 1. Calculate Opening Balance (Now uses caching internally) ---
#     opening_balance = calculate_account_balance_upto(account, start_date)
#     # Logging already handled within calculate_account_balance_upto
#
#     # --- 2. Fetch Ledger Entries within the Period ---
#     ledger_lines_query = VoucherLine.objects.filter(
#         account=account,
#         voucher__status=TransactionStatus.POSTED
#     ).select_related('voucher').order_by(
#         'voucher__date', 'voucher__created_at', 'pk'
#     )
#
#     if start_date:
#         ledger_lines_query = ledger_lines_query.filter(voucher__date__gte=start_date)
#     if end_date:
#         ledger_lines_query = ledger_lines_query.filter(voucher__date__lte=end_date)
#
#     ledger_lines = list(ledger_lines_query)
#
#     # --- 3. Process Entries and Calculate Running Balance & Period Totals ---
#     entries: List[Dict] = []
#     running_balance: Decimal = opening_balance
#     period_total_debit: Decimal = Decimal('0.00')
#     period_total_credit: Decimal = Decimal('0.00')
#     is_debit_nature_account: bool = account.is_debit_nature
#
#     for line in ledger_lines:
#         debit_amount = line.amount if line.dr_cr == DrCrType.DEBIT.name else Decimal('0.00')
#         credit_amount = line.amount if line.dr_cr == DrCrType.CREDIT.name else Decimal('0.00')
#
#         balance_change = Decimal('0.00')
#         if debit_amount > Decimal('0.00'):
#             balance_change = debit_amount if is_debit_nature_account else -debit_amount
#             period_total_debit += debit_amount
#         elif credit_amount > Decimal('0.00'):
#             balance_change = -credit_amount if is_debit_nature_account else credit_amount
#             period_total_credit += credit_amount
#
#         running_balance += balance_change
#
#         entries.append({
#             'line_pk': line.pk,
#             'date': line.voucher.date,
#             'voucher_pk': line.voucher.pk,
#             'voucher_number': line.voucher.voucher_number,
#             'narration': line.voucher.narration or line.narration or '',
#             'reference': line.voucher.reference or '',
#             'debit': debit_amount,
#             'credit': credit_amount,
#             'running_balance': running_balance
#         })
#
#     closing_balance = running_balance
#     logger.debug(f"Closing Balance (at end of {end_date or 'period'}): {closing_balance}")
#     logger.debug(f"Period Totals for Account {account.pk}: Debit={period_total_debit}, Credit={period_total_credit}")
#
#     # --- 4. Assemble Final Response Data ---
#     return {
#         'account': account,
#         'start_date': start_date,
#         'end_date': end_date,
#         'opening_balance': opening_balance,
#         'total_debit': period_total_debit,
#         'total_credit': period_total_credit,
#         'entries': entries,
#         'closing_balance': closing_balance,
#     }
=======
        'opening_balance_display': {'amount': opening_balance, 'dr_cr': opening_balance_dr_cr},
        'total_debit': period_total_debit,
        'total_credit': period_total_credit,
        'entries': entries,
        'closing_balance_display': {'amount': closing_balance, 'dr_cr': closing_balance_dr_cr},
    }
>>>>>>> 6bf6cecba810d211bb58ec8cdc516eeae683c30c
