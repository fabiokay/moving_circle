# Moving Circle Survivor

A simple yet engaging 2D survival game built with Pygame. Control a circle, shoot at incoming enemies, collect particles they drop, and purchase upgrades to survive longer!

## How to Play

*   **Movement:**
    *   `W`: Move Up
    *   `A`: Move Left
    *   `S`: Move Down
    *   `D`: Move Right
*   **Shooting:**
    *   `SPACEBAR`: Automatically targets and shoots at the nearest enemy.
*   **Goal:** Survive as long as possible by destroying enemies.
*   **Upgrades:**
    *   Enemies drop gold particles when defeated.
    *   Collect these particles to fill the bar at the top of the screen.
    *   Once the bar is full, an **Upgrade Store** will appear.
    *   Click on an upgrade to purchase it. The cost to fill the bar for the next upgrade will increase.
    *   Click "Continue Game" or press `ESCAPE` to close the store if you don't want to purchase an upgrade.

## Features

*   **Player Control:** Smooth WASD movement for the player's circle.
*   **Auto-Target Shooting:** Press space to automatically fire projectiles at the closest enemy.
*   **Diverse Enemies:**
    *   **Triangles:** Basic enemies that move towards the player.
    *   **Squares:** Tougher enemies that require multiple hits to destroy and change color when damaged. They often spawn in groups.
*   **Particle Pickups:** Defeated enemies drop gold particles.
*   **Upgrade System:**
    *   Collect particles to fill a bar and access the upgrade store.
    *   Available upgrades:
        *   **Faster Shots:** Increases your rate of fire.
        *   **Player Speed+:** Increases your movement speed.
    *   The particle requirement for upgrades increases after each purchase.
*   **Dynamic Background:** The background color gradually transitions through a cycle of colors.
*   **Game Timer:** Tracks your survival time in the top-right corner.
*   **Progressive Difficulty:** More enemies spawn over time, and upgrades become more challenging to acquire.

## How to Run

1.  **Ensure Pygame is installed:**
    If you don't have Pygame installed, you can install it via pip:
    ```bash
    pip install pygame
    ```
2.  **Navigate to the directory** containing `moving_circle.py` (or whatever you've named your main game file).
3.  **Run the Python script:**
    ```bash
    python moving_circle.py
    ```

Enjoy the game!