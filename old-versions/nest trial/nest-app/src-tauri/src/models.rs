use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct Note {
    pub id: i64,
    pub parent_id: Option<i64>,
    pub title: String,
    pub content: String,
}
