#![no_main]
#![no_std]

extern crate alloc;

use alloc::string::ToString;
use alloc::vec;
use casper_contract::{
    contract_api::{
        runtime::{self, call_contract, get_caller},
        storage::{self, dictionary_get, dictionary_put},
    },
    unwrap_or_revert::UnwrapOrRevert,
};
use casper_types::{
    account::AccountHash, runtime_args, ApiError, CLType, CLTyped, EntryPoint, EntryPointAccess,
    EntryPointType, EntryPoints, Parameter, RuntimeArgs, U512,
};

pub const PLAYER_MOVE: &str = "player_move";
pub const GUEST: &str = "guest";
pub const HOST: &str = "host";
pub const SCORE_DICTIONARY: &str = "score_dictionary";

pub enum T3Error {
    WrongTurnOrder = 0,
    MissedVictory = 1,
    OccupiedField = 2,
    NotHostedGame = 3,
}

impl From<T3Error> for ApiError {
    fn from(err: T3Error) -> ApiError {
        ApiError::User(err as u16)
    }
}
#[no_mangle]
pub extern "C" fn constructor() {
    storage::new_dictionary(SCORE_DICTIONARY).unwrap_or_revert();
}

#[no_mangle]
pub extern "C" fn host_move() {
    let host_hash = get_caller();
    let host = host_hash.to_string();
    let player_move: usize = runtime::get_named_arg::<u8>(PLAYER_MOVE) as usize;
    let guest_hash: AccountHash = runtime::get_named_arg(GUEST);
    let guest = guest_hash.to_string();

    let dictionary_uref = match runtime::get_key(&host) {
        Some(uref_key) => uref_key.into_uref().unwrap_or_revert(),
        None => storage::new_dictionary(&host).unwrap_or_revert(),
    };
    if let Some(Some(mut state)) =
        dictionary_get::<Option<[u8; 9]>>(dictionary_uref, &guest).unwrap_or_revert()
    {
        // caller hosts
        if state[player_move] == 0 {
            let move_count = state.iter().filter(|&e| *e == 0_u8).count();
            if move_count % 2 == 1 {
                state[player_move] = 1;
                match check_winner(state) {
                    1 => {
                        score_change(&host, &guest, 1_u8);
                        dictionary_put(dictionary_uref, &guest, Option::<[u8; 9]>::None)
                    }
                    2 => {
                        // you cannot win in the opponents turn
                        runtime::revert(T3Error::MissedVictory);
                    }
                    _ => dictionary_put(dictionary_uref, &guest, Some(state)),
                }
                // host turn
            } else {
                runtime::revert(T3Error::WrongTurnOrder);
                // guest turn
            }
        } else {
            runtime::revert(T3Error::OccupiedField);
        }
    }else{
        let mut state = [0_u8;9];
        state[player_move] = 1;
        dictionary_put(dictionary_uref, &guest, Some(state))
    }
}

#[no_mangle]
pub extern "C" fn guest_move() {
    let guest_hash = get_caller();
    let guest = guest_hash.to_string();
    let player_move: usize = runtime::get_named_arg::<u8>(PLAYER_MOVE) as usize;
    let host_hash: AccountHash = runtime::get_named_arg(HOST);
    let host = host_hash.to_string();

    let dictionary_uref = runtime::get_key(&host)
        .unwrap_or_revert()
        .into_uref()
        .unwrap_or_revert();
    if let Some(Some(mut state)) = dictionary_get::<Option<[u8; 9]>>(dictionary_uref, &guest).unwrap_or_revert() {
        // caller is guest
        if state[player_move] == 0 {
            let move_count = state.iter().filter(|&e| *e == 0_u8).count();
            if move_count % 2 == 0 {
                // guest turn
                state[player_move] = 2;
                match check_winner(state) {
                    2 => {
                        score_change(&host, &guest, 2_u8);
                        dictionary_put(dictionary_uref, &guest, Option::<[u8; 9]>::None)
                    }
                    1 => {
                        // you cannot win in the opponents turn
                        runtime::revert(T3Error::MissedVictory);
                    }
                    _ => dictionary_put(dictionary_uref, &guest, Some(state)),
                }
            } else {
                // host turn
                runtime::revert(T3Error::WrongTurnOrder);
            }
        } else {
            runtime::revert(T3Error::OccupiedField);
        }
    }else{
        runtime::revert(T3Error::NotHostedGame);
    }
}

#[no_mangle]
pub extern "C" fn call() {
    let mut entry_points = EntryPoints::new();
    entry_points.add_entry_point(EntryPoint::new(
        "constructor",
        vec![],
        CLType::Unit,
        EntryPointAccess::Public,
        EntryPointType::Contract,
    ));
    entry_points.add_entry_point(EntryPoint::new(
        "host_move",
        vec![
            Parameter::new(PLAYER_MOVE, u8::cl_type()),
            Parameter::new(GUEST, AccountHash::cl_type()),
        ],
        CLType::Unit,
        EntryPointAccess::Public,
        EntryPointType::Contract,
    ));
    entry_points.add_entry_point(EntryPoint::new(
        "guest_move",
        vec![
            Parameter::new(PLAYER_MOVE, u8::cl_type()),
            Parameter::new(HOST, AccountHash::cl_type()),
        ],
        CLType::Unit,
        EntryPointAccess::Public,
        EntryPointType::Contract,
    ));
    let (contract_hash, _version) = storage::new_contract(
        entry_points,
        None,
        Some("tictactoe_contract_package_hash".to_string()),
        Some("tictactoe_access_token".to_string()),
    );
    runtime::put_key("tictactoe_contract", contract_hash.into());
    runtime::put_key(
        "tictactoe_contract_wrapped",
        storage::new_uref(contract_hash).into(),
    );
    call_contract(contract_hash, "constructor", runtime_args! {})
}

/*
|0|1|2|
-------
|3|4|5|
-------
|6|7|8|
*/
pub fn check_winner(match_table: [u8; 9]) -> u8 {
    if match_table[0] == match_table[1] && match_table[1] == match_table[2] && match_table[2] == 1
        || match_table[3] == match_table[4]
            && match_table[4] == match_table[5]
            && match_table[5] == 1
        || match_table[6] == match_table[7]
            && match_table[7] == match_table[8]
            && match_table[8] == 1
        || match_table[0] == match_table[3]
            && match_table[3] == match_table[6]
            && match_table[6] == 1
        || match_table[1] == match_table[4]
            && match_table[4] == match_table[7]
            && match_table[7] == 1
        || match_table[2] == match_table[5]
            && match_table[5] == match_table[8]
            && match_table[8] == 1
        || match_table[0] == match_table[4]
            && match_table[4] == match_table[8]
            && match_table[8] == 1
        || match_table[2] == match_table[4]
            && match_table[4] == match_table[6]
            && match_table[6] == 1
    {
        1
    }
    else if match_table[0] == match_table[1] && match_table[1] == match_table[2] && match_table[2] == 2
        || match_table[3] == match_table[4]
            && match_table[4] == match_table[5]
            && match_table[5] == 2
        || match_table[6] == match_table[7]
            && match_table[7] == match_table[8]
            && match_table[8] == 2
        || match_table[0] == match_table[3]
            && match_table[3] == match_table[6]
            && match_table[6] == 2
        || match_table[1] == match_table[4]
            && match_table[4] == match_table[7]
            && match_table[7] == 2
        || match_table[2] == match_table[5]
            && match_table[5] == match_table[8]
            && match_table[8] == 2
        || match_table[0] == match_table[4]
            && match_table[4] == match_table[8]
            && match_table[8] == 2
        || match_table[2] == match_table[4]
            && match_table[4] == match_table[6]
            && match_table[6] == 2
    {
        2
    }else{
        0
    }
}

fn score_change(host: &str, guest: &str, winner: u8) {
    let dictionary_uref = match runtime::get_key(SCORE_DICTIONARY) {
        Some(uref_key) => uref_key.into_uref().unwrap_or_revert(),
        None => storage::new_dictionary(SCORE_DICTIONARY).unwrap_or_revert(),
    };
    // host score
    let host_score = dictionary_get::<U512>(dictionary_uref, host)
        .unwrap_or_revert()
        .unwrap_or_default();
    dictionary_put(
        dictionary_uref,
        host,
        if winner == 1 {
            host_score + U512::one()
        } else {
            host_score.saturating_sub(U512::one())
        },
    );

    // guest score
    let guest_score = dictionary_get::<U512>(dictionary_uref, guest)
        .unwrap_or_revert()
        .unwrap_or_default();
    dictionary_put(
        dictionary_uref,
        guest,
        if winner == 2 {
            guest_score + U512::one()
        } else {
            guest_score.saturating_sub(U512::one())
        },
    );
}
