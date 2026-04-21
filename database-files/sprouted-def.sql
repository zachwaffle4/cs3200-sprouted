DROP DATABASE IF EXISTS sprouted;
CREATE DATABASE sprouted;
USE sprouted;

-- Independent / Parent Tables

CREATE TABLE Garden_Site
(
    site_id INT AUTO_INCREMENT PRIMARY KEY,
    site_name VARCHAR(120) NOT NULL,
    street VARCHAR(200) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50)  NOT NULL,
    zip VARCHAR(10)  NOT NULL
);

CREATE TABLE Crop
(
    crop_id INT AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(120) NOT NULL,
    crop_type VARCHAR(80)  NOT NULL
);

CREATE TABLE User
(
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    role VARCHAR(50) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    phone VARCHAR(20),
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL
);

CREATE TABLE Organization
(
    org_id INT AUTO_INCREMENT PRIMARY KEY,
    org_name VARCHAR(150) NOT NULL,
    org_type VARCHAR(80),
    contact_name VARCHAR(150),
    contact_email VARCHAR(200),
    contact_phone VARCHAR(20),
    address VARCHAR(250)
);

-- Tables that depend on Garden_Site

CREATE TABLE Plot
(
    plot_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    site_id INT NOT NULL,
    CONSTRAINT fk_plot_site
        FOREIGN KEY (site_id) REFERENCES Garden_Site (site_id)
);

CREATE TABLE Workday
(
    workday_id INT AUTO_INCREMENT PRIMARY KEY,
    site_id INT NOT NULL,
    event_name VARCHAR(150) NOT NULL,
    event_date DATE NOT NULL,
    description TEXT,
    volunteers_needed INT DEFAULT 0,
    start_time TIME,
    end_time TIME,
    CONSTRAINT fk_workday_site
        FOREIGN KEY (site_id) REFERENCES Garden_Site (site_id)
);

-- Tables that depend on Plot and/or Crop

CREATE TABLE Watering_Schedule
(
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT NOT NULL,
    crop_id INT,
    frequency VARCHAR(80),
    time_of_day VARCHAR(50),
    method VARCHAR(80),
    notes TEXT,
    CONSTRAINT fk_water_plot
        FOREIGN KEY (plot_id) REFERENCES Plot (plot_id),
    CONSTRAINT fk_water_crop
        FOREIGN KEY (crop_id) REFERENCES Crop (crop_id)
);

CREATE TABLE Harvest
(
    harvest_id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT NOT NULL,
    crop_id INT NOT NULL,
    harvest_date DATE NOT NULL,
    quantity_lbs DECIMAL(10, 2) DEFAULT 0,
    CONSTRAINT fk_harvest_plot
        FOREIGN KEY (plot_id) REFERENCES Plot (plot_id),
    CONSTRAINT fk_harvest_crop
        FOREIGN KEY (crop_id) REFERENCES Crop (crop_id)
);

CREATE TABLE Pest_Report (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT NOT NULL,
    crop_id INT,
    user_id INT,
    description TEXT,
    severity VARCHAR(50),
    date_reported DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'open',
    CONSTRAINT fk_pest_plot
        FOREIGN KEY (plot_id) REFERENCES Plot(plot_id),
    CONSTRAINT fk_pest_crop
        FOREIGN KEY (crop_id) REFERENCES Crop(crop_id),
    CONSTRAINT fk_pest_user
        FOREIGN KEY (user_id) REFERENCES User(user_id)
);

CREATE TABLE Plot_Assignment (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT NOT NULL,
    user_id INT NOT NULL,
    assigned_date DATE NOT NULL,
    end_date DATE,
    CONSTRAINT fk_assign_plot
        FOREIGN KEY (plot_id) REFERENCES Plot(plot_id),
    CONSTRAINT fk_assign_user
        FOREIGN KEY (user_id) REFERENCES User(user_id)
);

-- Yield 

CREATE TABLE Yield (
    plot_id INT NOT NULL,
    crop_id INT NOT NULL,
    total_quantity DECIMAL(10,2) DEFAULT 0,
    PRIMARY KEY (plot_id, crop_id),
    CONSTRAINT fk_yield_plot
        FOREIGN KEY (plot_id) REFERENCES Plot(plot_id),
    CONSTRAINT fk_yield_crop
        FOREIGN KEY (crop_id) REFERENCES Crop(crop_id)
);

-- Surplus / Produce / Pickup chain

CREATE TABLE Surplus_Listing (
    listing_id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT NOT NULL,
    crop_id INT NOT NULL,
    quantity_lbs DECIMAL(10,2) DEFAULT 0,
    listed_date DATE NOT NULL,
    freshness_note TEXT,
    status VARCHAR(50) DEFAULT 'available',
    CONSTRAINT fk_surplus_plot
        FOREIGN KEY (plot_id) REFERENCES Plot(plot_id),
    CONSTRAINT fk_surplus_crop
        FOREIGN KEY (crop_id) REFERENCES Crop(crop_id)
);

CREATE TABLE Produce_Request (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    org_id INT NOT NULL,
    listing_id INT NOT NULL,
    requested_date DATE NOT NULL,
    preferred_pickup_date DATE,
    status VARCHAR(50) DEFAULT 'pending',
    CONSTRAINT fk_req_org
        FOREIGN KEY (org_id) REFERENCES Organization(org_id),
    CONSTRAINT fk_req_listing
        FOREIGN KEY (listing_id) REFERENCES Surplus_Listing(listing_id)
);

CREATE TABLE Pickup (
    pickup_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL UNIQUE,
    pickup_date DATE NOT NULL,
    qty_received_lbs DECIMAL(10,2) DEFAULT 0,
    quality_rating INT,
    notes TEXT,
    CONSTRAINT fk_pickup_req
        FOREIGN KEY (request_id) REFERENCES Produce_Request(request_id)
);

-- Plot applications and waitlist

CREATE TABLE Plot_Application (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    plot_id        INT,
    requested_date DATE NOT NULL,
    status         VARCHAR(20) NOT NULL DEFAULT 'pending',
    CONSTRAINT fk_app_user
        FOREIGN KEY (user_id) REFERENCES User (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_app_plot
        FOREIGN KEY (plot_id) REFERENCES Plot (plot_id) ON DELETE SET NULL
);

-- Workday-related: Tasks and Signups

CREATE TABLE Workday_Task (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    workday_id INT NOT NULL,
    task_description TEXT NOT NULL,
    location_note VARCHAR(200),
    urgency VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    CONSTRAINT fk_task_workday
        FOREIGN KEY (workday_id) REFERENCES Workday(workday_id)
);

CREATE TABLE Event_Signup (
    signup_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    workday_id INT NOT NULL,
    signup_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'registered',
    CONSTRAINT fk_signup_user
        FOREIGN KEY (user_id) REFERENCES User(user_id),
    CONSTRAINT fk_signup_workday
        FOREIGN KEY (workday_id) REFERENCES Workday(workday_id)
);

-- Volunteer logging

CREATE TABLE Volunteer_Log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    task_id INT,
    work_date DATE NOT NULL,
    hours_logged DECIMAL(5,2) DEFAULT 0,
    notes TEXT,
    CONSTRAINT fk_log_user
        FOREIGN KEY (user_id) REFERENCES User(user_id),
    CONSTRAINT fk_log_task
        FOREIGN KEY (task_id) REFERENCES Workday_Task(task_id)
);
