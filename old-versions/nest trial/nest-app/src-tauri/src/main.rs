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


#[tauri::command]
fn create_note(title: String, parent_id: Option<i64>, state: State<AppState>) -> Result<Note, String> {
    let conn = state.db.lock().unwrap();
    conn.execute(
        "INSERT INTO notes (title, parent_id) VALUES (?1, ?2)",
        rusqlite::params![title, parent_id],
    )
    .map_err(|e| e.to_string())?;

    let id = conn.last_insert_rowid();
    let mut stmt = conn
        .prepare("SELECT id, parent_id, title, content FROM notes WHERE id = ?1")
        .map_err(|e| e.to_string())?;

    let note = stmt
        .query_row([id], |row| {
            Ok(Note {
                id: row.get(0)?,
                parent_id: row.get(1)?,
                title: row.get(2)?,
                content: row.get(3)?,
            })
        })
        .map_err(|e| e.to_string())?;

    Ok(note)
}

#[tauri::command]
fn delete_note(id: i64, state: State<AppState>) -> Result<(), String> {
    let mut conn = state.db.lock().unwrap();
    // This is a recursive delete, so we need to be careful.
    // We'll start a transaction to ensure that all deletes succeed or none do.
    let tx = conn.transaction().map_err(|e| e.to_string())?;

    // First, find all children of the node to be deleted.
    let mut children_to_delete = vec![id];
    let mut i = 0;
    while i < children_to_delete.len() {
        let parent_id = children_to_delete[i];
        let mut stmt = tx
            .prepare("SELECT id FROM notes WHERE parent_id = ?1")
            .map_err(|e| e.to_string())?;
        let child_iter = stmt
            .query_map([parent_id], |row| row.get(0))
            .map_err(|e| e.to_string())?;
        for child_id in child_iter {
            children_to_delete.push(child_id.map_err(|e| e.to_string())?);
        }
        i += 1;
    }

    // Now delete all the nodes, starting from the leaves.
    for id_to_delete in children_to_delete.iter().rev() {
        tx.execute("DELETE FROM notes WHERE id = ?1", [id_to_delete])
            .map_err(|e| e.to_string())?;
    }

    tx.commit().map_err(|e| e.to_string())
}

#[tauri::command]
fn update_note_parent(id: i64, parent_id: Option<i64>, state: State<AppState>) -> Result<(), String> {
    let conn = state.db.lock().unwrap();
    conn.execute(
        "UPDATE notes SET parent_id = ?1 WHERE id = ?2",
        rusqlite::params![parent_id, id],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn update_note_content(id: i64, content: String, state: State<AppState>) -> Result<(), String> {
    let conn = state.db.lock().unwrap();
    conn.execute(
        "UPDATE notes SET content = ?1 WHERE id = ?2",
        rusqlite::params![content, id],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
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
            get_child_notes,
            create_note,
            delete_note,
            update_note_parent,
            update_note_content
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
