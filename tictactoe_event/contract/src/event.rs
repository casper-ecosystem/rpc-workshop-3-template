use alloc::{
    collections::BTreeMap,
    string::{String, ToString},
};
use casper_contract::contract_api::{runtime, storage};
use casper_types::{URef, U512};

use crate::{EVENT_TYPE, GUEST, GUEST_SCORE, HOST, HOST_SCORE, PLAYER_MOVE};

pub enum T3Event {
    GameStart {
        host: String,
        guest: String,
        player_move: usize,
    },
    HostVictory {
        host: String,
        guest: String,
        host_score: U512,
        guest_score: U512,
    },
    GuestVictory {
        host: String,
        guest: String,
        host_score: U512,
        guest_score: U512,
    },
    HostMove {
        host: String,
        guest: String,
        player_move: usize,
    },
    GuestMove {
        host: String,
        guest: String,
        player_move: usize,
    },
    Draw {
        host: String,
        guest: String,
    },
    Reset {
        host: String,
        guest: String,
    },
    InitContract,
}

pub fn emit(event: &T3Event) {
    let push_event = match event {
        T3Event::HostVictory {
            host,
            guest,
            host_score,
            guest_score,
        } => {
            let mut param = BTreeMap::new();
            param.insert(HOST, host.to_string());
            param.insert(GUEST, guest.to_string());
            param.insert(HOST_SCORE, host_score.to_string());
            param.insert(GUEST_SCORE, guest_score.to_string());
            param.insert(EVENT_TYPE, "HostVictory".to_string());
            param
        }
        T3Event::GuestVictory {
            host,
            guest,
            host_score,
            guest_score,
        } => {
            let mut param = BTreeMap::new();
            param.insert(HOST, host.to_string());
            param.insert(GUEST, guest.to_string());
            param.insert(HOST_SCORE, host_score.to_string());
            param.insert(GUEST_SCORE, guest_score.to_string());
            param.insert(EVENT_TYPE, "GuestVictory".to_string());
            param
        }
        T3Event::GameStart {
            host,
            guest,
            player_move,
        } => {
            let mut param = BTreeMap::new();
            param.insert(HOST, host.to_string());
            param.insert(GUEST, guest.to_string());
            param.insert(PLAYER_MOVE, player_move.to_string());
            param.insert(EVENT_TYPE, "GameStart".to_string());
            param
        }
        T3Event::HostMove {
            host,
            guest,
            player_move,
        } => {
            let mut param = BTreeMap::new();
            param.insert(HOST, host.to_string());
            param.insert(GUEST, guest.to_string());
            param.insert(PLAYER_MOVE, player_move.to_string());
            param.insert(EVENT_TYPE, "HostMove".to_string());
            param
        }
        T3Event::GuestMove {
            host,
            guest,
            player_move,
        } => {
            let mut param = BTreeMap::new();
            param.insert(HOST, host.to_string());
            param.insert(GUEST, guest.to_string());
            param.insert(PLAYER_MOVE, player_move.to_string());
            param.insert(EVENT_TYPE, "GuestMove".to_string());
            param
        }
        T3Event::Draw { host, guest } => {
            let mut param = BTreeMap::new();
            param.insert(HOST, host.to_string());
            param.insert(GUEST, guest.to_string());
            param.insert(EVENT_TYPE, "Draw".to_string());
            param
        }
        T3Event::Reset { host, guest } => {
            let mut param = BTreeMap::new();
            param.insert(HOST, host.to_string());
            param.insert(GUEST, guest.to_string());
            param.insert(EVENT_TYPE, "Reset".to_string());
            param
        }
        T3Event::InitContract => {
            let mut param = BTreeMap::new();
            param.insert(EVENT_TYPE, "InitContract".to_string());
            param
        }
    };
    let latest_event: URef = storage::new_uref(push_event);
    runtime::put_key("latest_event", latest_event.into());
}
