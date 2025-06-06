# Moving Circle Survivor

A dynamic 2D survival game built with Pygame. Choose your vessel, automatically shoot at incoming enemies on a tiled map, collect particles they drop, level up, and purchase upgrades to survive as long as possible!

## How to Play

*   **Character Selection:** At the start, choose one of three "Vessels," each with a unique color and shooting style.
*   **Movement:**
    *   `W`: Move Up
    *   `A`: Move Left
    *   `S`: Move Down
    *   `D`: Move Right
*   **Shooting:**
    *   **Automatic!** Your chosen vessel will automatically target and shoot at enemies when they are in range and your weapon is ready.
*   **Goal:** Survive as long as possible by destroying enemies.
*   **Upgrades:**
    *   Enemies drop gold particles when defeated.
    *   Collect these particles to fill the bar at the top of the screen.
    *   Once the bar is full, an **Upgrade Store** will appear.
    *   Click on an upgrade to purchase it. The cost to fill the bar for the next upgrade will increase.
    *   Click "Continue Game" or press `ESCAPE` to close the store if you don't want to purchase an upgrade.
*   **World:** Navigate a bounded map made of tiled background images. Don't fall off the edge! (Just kidding, you can't).

## Features

*   **Character Selection:** Choose from different vessels, each with unique shooting mechanics:
    *   **Standard:** Reliable single shot.
    *   **Spread:** Fires three projectiles in a cone.
    *   **Burst:** Unleashes projectiles in all directions.
*   **Player Control:** Smooth WASD movement for the player's circle.
*   **Automatic Auto-Target Shooting:** Your vessel automatically fires projectiles at the closest enemy (or in a pattern, depending on the vessel).
*   **Diverse Enemies:**
    *   **Triangles:** Basic enemies that move towards the player.
    *   **Squares:** Tougher enemies that require multiple hits to destroy and change color when damaged. They often spawn in groups.
*   **Particle Pickups:** Defeated enemies drop gold particles. Special pink particles are worth double!
*   **Upgrade System:**
    *   Collect particles to fill a bar and access the upgrade store.
    *   Available upgrades:
        *   **Faster Shots:** Increases your rate of fire.
        *   **Player Speed+:** Increases your movement speed.
        *   **Pickup Radius+:** Increases the radius for collecting particles, making it easier to gather them.
    *   The particle requirement for upgrades increases after each purchase.
*   **Player Leveling:** Increase your level each time you fill the pickup bar.
*   **Tiled Map & Camera:** The game world is a scrollable, tiled map with defined boundaries. The camera follows the player.
*   **Dynamic Background Color:** The base background color under the map gradually transitions through a cycle of colors.
*   **Game Timer:** Tracks your survival time in the top-right corner.
*   **Progressive Difficulty:** More enemies spawn over time, and upgrades become more challenging to acquire.
*   **Sound Effects:** Audio cues for shooting, picking up items, enemy hits, and player death.

## How to Run

1.  **Ensure Pygame is installed:**
    If you don't have Pygame (version 2.x.x recommended for `pygame.Color.lerp`) installed, you can install it via pip:
    ```bash
    pip install pygame
    ```
2.  **Navigate to the directory** containing `moving_circle.py` (or whatever you've named your main game file).
3.  **Run the Python script:**
    ```bash
    python moving_circle.py
    ```

## Future additions

1.  Parallax background for a more realistic depth effect
2.  Even more game sounds
3.  Background music
4.  More upgrade, more weapons
5.  Tech tree based upgrade system
6.  


Enjoy the game!