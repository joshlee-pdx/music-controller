import React, { Component } from 'react';
import { Grid, Button, Typography } from '@material-ui/core';
import CreateRoomPage from "./CreateRoomPage";
import MusicPlayer from "./MusicPlayer";

export default class Room extends Component {
  constructor(props) {
    super(props);
    this.state = {
      votesToSkip: 2,
      guestCanPause: false,
      isHost: false,
      showSettings: false,
      spotifyAuthenticated: false,
      song: {},
    };
    // Get room code for current room
    this.roomCode = this.props.match.params.roomCode;

    // Bind functions to this
    this.leaveButtonPressed = this.leaveButtonPressed.bind(this);
    this.updateShowSettings = this.updateShowSettings.bind(this);
    this.renderSettingsButton = this.renderSettingsButton.bind(this);
    this.renderSettings = this.renderSettings.bind(this);
    this.getRoomDetails = this.getRoomDetails.bind(this);
    this.authenticateSpotify = this.authenticateSpotify.bind(this);
    this.getCurrentSong = this.getCurrentSong.bind(this);

    // Display current room details
    this.getRoomDetails();
  }

  // Once component has loaded, start interval to refresh current song info every second
  componentDidMount() {
    this.interval = setInterval(this.getCurrentSong, 1000);
  }

  // Clear interval once page is left
  componentWillUnmount() {
    clearInterval(this.interval);
  }

  getRoomDetails() {
    fetch('/api/get-room' + '?code=' + this.roomCode)
    .then((response) => {
      // Check if valid room
      if(!response.ok){
        this.props.leaveRoomCallback(); // Clear state on homepage
        this.props.history.push("/");   // Redirect to homepage
      }  
      
      return response.json();
    })
    .then((data) => {
      this.setState({
        votesToSkip: data.votes_to_skip,
        guestCanPause: data.guest_can_pause,
        isHost: data.is_host,
      });

      if(this.state.isHost) // Authenticate user only if they are the host after state is set
        this.authenticateSpotify();
    });
  }

  // Check to see if user is authenticated, and if not, authenticate them
  authenticateSpotify() {
    fetch('/spotify/is-authenticated')
      .then((response) => response.json())
      .then((data)=>{
        this.setState({spotifyAuthenticated: data.status});
        if(!data.status){ // If not authenticated, then authenticate
          fetch('/spotify/get-auth-url')
            .then((response) => response.json())
            .then((data)=> {
              window.location.replace(data.url); // Redirect to spotify page
            });
        }
      });
  }

  // Get current song information
  getCurrentSong() {
    fetch("/spotify/current-song")
      .then((response) => {
        if (!response.ok) {
          return {};
        } else {
          return response.json();
        }
      })
      .then((data) => {
        this.setState({ song: data });
        console.log(data);
      });
  }

  leaveButtonPressed (){
    const requestOptions = {
      method: "POST",
      headers: {"Content-Type": "application/json"},
    };
  
    fetch('/api/leave-room', requestOptions).then((_response) => {
      this.props.leaveRoomCallback(); // Clear state on homepage
      this.props.history.push("/");   // Redirect to homepage
    });
  }

  updateShowSettings(value) {
    this.setState({
      showSettings: value,
    });
  }

  renderSettings() {
    return (
      <Grid container spacing={1}>
        <Grid item xs={12} align="center">
          <CreateRoomPage 
            update={true} 
            votesToSkip={this.state.votesToSkip} 
            guestCanPause={this.state.guestCanPause} 
            roomCode={this.roomCode} 
            updateCallback={this.getRoomDetails}
          />
        </Grid>

        <Grid item xs={12} align="center">
          <Button variant="contained" color="secondary" onClick={() => this.updateShowSettings(false)}>Close</Button>
        </Grid>
      </Grid>
    );
  }

  renderSettingsButton() {
    return(
      <Grid item xs={12} align="center">
        <Button 
          variant="contained" 
          color="primary" 
          onClick={() => this.updateShowSettings(true)}
        >
            Settings
        </Button>
      </Grid>
    )
  }

  render() {
    if(this.state.showSettings){
      return this.renderSettings();
    }
    return (
      <Grid container spacing={1}> 
        <Grid item xs={12} align="center">
          <Typography variant="h4" component="h4">
            Code: {this.roomCode}
          </Typography>
        </Grid>

        <MusicPlayer {...this.state.song} />

        {this.state.isHost ? this.renderSettingsButton() : null}

        <Grid item xs={12} align="center">
          <Button variant="contained" color="secondary" onClick={this.leaveButtonPressed}>Leave Room</Button>
        </Grid>

      </Grid>
    );
  }
}

