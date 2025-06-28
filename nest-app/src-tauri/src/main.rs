// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
pub mod models;

// Add these new 'use' statements at the top of src-tauri/src/main.rs
use rusqlite::Connection;
use std::fs;
use std::sync::Mutex;
use tauri::State;
use rusqlite::Result;
use models::Note;
use tauri::Manager;


// Struct to hold the database connection state
pub struct AppState {
    db: Mutex<Connection>,
}

// Tauri command to get top-level notes
#[tauri::command]
fn get_top_level_notes(state: State<AppState>) -> Result<Vec<Note>, String> {
    let conn = state.db.lock().unwrap();
    let mut stmt = conn
        .prepare("SELECT id, parent_id, title, content FROM notes WHERE parent_id IS NULL")
        .map_err(|e| e.to_string())?;

    let note_iter = stmt
        .query_map([], |row| {
            Ok(Note {
                id: row.get(0)?,
                parent_id: row.get(1)?,
                title: row.get(2)?,
                content: row.get(3)?,
            })
        })
        .map_err(|e| e.to_string())?;

    let mut notes = Vec::new();
    for note in note_iter {
        notes.push(note.map_err(|e| e.to_string())?);
    }
    Ok(notes)
}

#[tauri::command]
fn get_child_notes(parent_id: i64, state: State<AppState>) -> Result<Vec<Note>, String> {
    let conn = state.db.lock().unwrap();
    let mut stmt = conn
        .prepare("SELECT id, parent_id, title, content FROM notes WHERE parent_id = ?1")
        .map_err(|e| e.to_string())?;

    let note_iter = stmt
        .query_map([parent_id], |row| {
            Ok(Note {
                id: row.get(0)?,
                parent_id: row.get(1)?,
                title: row.get(2)?,
                content: row.get(3)?,
            })
        })
        .map_err(|e| e.to_string())?;

    let mut notes = Vec::new();
    for note in note_iter {
        notes.push(note.map_err(|e| e.to_string())?);
    }
    Ok(notes)
}


fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let handle = app.handle();
            let app_data_dir = handle.path().app_data_dir()
                .expect("The app data directory should exist.");
            
            fs::create_dir_all(&app_data_dir).expect("Failed to create app data directory.");
            let db_path = app_data_dir.join("nest.db");

            let conn = Connection::open(db_path).expect("Failed to open database.");

            conn.execute(
                "CREATE TABLE IF NOT EXISTS notes (
                    id        INTEGER PRIMARY KEY,
                    parent_id INTEGER,
                    title     TEXT NOT NULL,
                    content   TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (parent_id) REFERENCES notes (id)
                )",
                (),
            )
            .expect("Failed to create 'notes' table.");

            app.manage(AppState {
                db: Mutex::new(conn),
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_top_level_notes,
            get_child_notes
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
