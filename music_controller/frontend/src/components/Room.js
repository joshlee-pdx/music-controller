import React, { Component } from 'react';
import { Grid, Button, Typography } from '@material-ui/core';

export default class Room extends Component {
  constructor(props) {
    super(props);
    this.state = {
      votesToSkip: 2,
      guestCanPause: false,
      isHost: false,
    };
    this.roomCode = this.props.match.params.roomCode;
    this.getRoomDetails();
    this.leaveButtonPressed = this.leaveButtonPressed.bind(this)
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

  render() {
    return (
      <Grid container spacing={1}> 
        <Grid item xs={12} align="center">
          <Typography variant="h4" component="h4">
            Code: {this.roomCode}
          </Typography>
        </Grid>

        <Grid item xs={12} align="center">
          <Typography variant="h6" component="h6">
            Votes: {this.state.votesToSkip}
          </Typography>
        </Grid>

        <Grid item xs={12} align="center">
          <Typography variant="h6" component="h6">
            Guest Can Pause: {this.state.guestCanPause.toString()}
          </Typography>
        </Grid>

        <Grid item xs={12} align="center">
          <Typography variant="h6" component="h6">
            Host: {this.state.isHost.toString()}
          </Typography>
          <Button variant="contained" color="secondary" onClick={this.leaveButtonPressed}>Leave Room</Button>
        </Grid>
      </Grid>
    );
  }
}

